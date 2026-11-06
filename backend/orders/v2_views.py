from decimal import Decimal
import logging
import threading
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from devs.models import ErrorLog
from dispatcher.models import SystemSettings
from riders.models import RiderEarning
from riders.notifications import notify_rider
from .permissions import IsRider
from sparky_utils.advice import exception_advice
from sparky_utils.exceptions import ServiceException
from sparky_utils.response import service_response
from wallet.models import Wallet

from .models import Order, Delivery
from .signals import order_event_signal

logger = logging.getLogger(__name__)

MAX_VERIFICATION_ATTEMPTS = 5


class OrderPickupV2Serializer(serializers.Serializer):
    order_number = serializers.CharField(required=True, max_length=20)
    pickup_code = serializers.CharField(required=True, max_length=10)

    def validate_pickup_code(self, value: str) -> str:
        val = value.strip()
        if not val.isdigit() or len(val) != 6:
            raise ServiceException(
                status_code=400,
                message="Pickup code must be a 6-digit numeric code.",
            )
        return val


class DeliveryCompleteV2Serializer(serializers.Serializer):
    drop_code = serializers.CharField(required=True, max_length=10)

    def validate_drop_code(self, value: str) -> str:
        val = value.strip()
        if not val.isdigit() or len(val) != 6:
            raise ServiceException(
                status_code=400,
                message="Drop code must be a 6-digit numeric code.",
            )
        return val


class OrderCompleteV2Serializer(serializers.Serializer):
    order_number = serializers.CharField(required=True, max_length=20)
    drop_code = serializers.CharField(required=True, max_length=10)

    def validate_drop_code(self, value: str) -> str:
        val = value.strip()
        if not val.isdigit() or len(val) != 6:
            raise ServiceException(
                status_code=400,
                message="Drop code must be a 6-digit numeric code.",
            )
        return val


def _finalize_order_completion(order: Order, rider, user) -> Decimal:
    """Finalize order completion: calculate rider earnings, update status, and notify."""
    settings_obj = SystemSettings.objects.first()
    commission_pct = (
        settings_obj.commission_pct if settings_obj else Decimal("20.00")
    )
    order_amount = Decimal(str(order.total_amount))
    commission_amount = (commission_pct / Decimal("100")) * order_amount
    net_earning = commission_amount

    # Record rider earnings (idempotent get_or_create).
    # The post_save signal on RiderEarning automatically credits the rider wallet.
    earning, created = RiderEarning.objects.get_or_create(
        order=order,
        defaults={
            "rider": rider,
            "base_fare": order_amount,
            "commission_pct": commission_pct,
            "commission_amount": commission_amount,
            "net_earning": commission_amount,
            "cod_amount": Decimal("0.00"),
        },
    )

    # Mark Order as Done
    old_status = order.status
    order.status = "Done"
    if not order.completed_at:
        order.completed_at = timezone.now()
    order.save(update_fields=["status", "completed_at", "updated_at"])

    # Log order event
    order_event_signal.send(
        sender=order.__class__,
        order=order,
        event="Order Completed (V2 Verified)",
        description=f"Order completed with verified drop code by rider {rider.rider_id}",
        old_value=old_status,
        new_value="Done",
        created_by=user,
    )

    # Trigger order-completed webhook in background
    def _trigger_completed_webhook():
        try:
            from webhooks.utils import trigger_webhook
            from .serializers import OrderSerializer

            payload = {
                "event": "order-completed",
                "timestamp": order.completed_at.isoformat(),
                "data": OrderSerializer(order).data,
            }
            trigger_webhook("order-completed", payload)
        except Exception as e:
            logger.error(f"Failed to trigger order-completed webhook in V2: {e}")

    threading.Thread(target=_trigger_completed_webhook, daemon=True).start()

    # Send push notification to rider in background
    def _notify_rider_completion():
        try:
            notify_rider(
                rider=rider,
                title="Order Completed 🎉",
                body=f"Order #{order.order_number} completed. ₦{net_earning} credited to your wallet.",
                data={
                    "order_number": order.order_number,
                    "net_earning": str(net_earning),
                },
            )
        except Exception as exc:
            logger.warning(f"Failed to send completion notification to rider: {exc}")

    threading.Thread(target=_notify_rider_completion, daemon=True).start()

    return net_earning


class OrderPickupV2View(APIView):
    """
    Rider marks an order as picked up by providing the 6-digit pickup code.
    POST /api/orders/v2/pickup/
    {
        "order_number": "6158001",
        "pickup_code": "123456"
    }
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
    def post(self, request: Request) -> Response:
        serializer = OrderPickupV2Serializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            first_err = next(iter(errors.values()))[0] if errors else "Invalid request data."
            raise ServiceException(status_code=400, message=str(first_err))

        order_number = serializer.validated_data["order_number"]
        pickup_code = serializer.validated_data["pickup_code"]

        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            raise ServiceException(status_code=403, message="Rider profile not found.")

        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            raise ServiceException(status_code=404, message="Order not found.")

        if order.rider_id != rider.id:
            raise ServiceException(
                status_code=403,
                message="You are not the assigned rider for this order.",
            )

        # Idempotent return if already picked up or fulfilling
        if order.status in ["PickedUp", "Fulfilling"]:
            return service_response(
                status="success",
                message="Order is already marked as picked up.",
                data={"order_number": order_number, "status": order.status},
                status_code=200,
            )

        if order.status in ["Done", "CustomerCanceled", "RiderCanceled", "Failed"]:
            raise ServiceException(
                status_code=400,
                message=f"Cannot pick up order in current status: {order.status}",
            )

        # Lock verification if max failed attempts reached
        if order.pickup_code_attempts >= MAX_VERIFICATION_ATTEMPTS:
            raise ServiceException(
                status_code=400,
                message="Pickup verification is locked due to too many failed attempts (maximum 5). Please contact support.",
            )

        # Compare pickup code
        if order.pickup_code != pickup_code:
            order.pickup_code_attempts += 1
            order.save(update_fields=["pickup_code_attempts", "updated_at"])
            remaining = MAX_VERIFICATION_ATTEMPTS - order.pickup_code_attempts
            if remaining <= 0:
                raise ServiceException(
                    status_code=400,
                    message="Incorrect pickup code. Verification is now locked after 5 failed attempts.",
                )
            raise ServiceException(
                status_code=400,
                message=f"Incorrect pickup code. {remaining} attempt(s) remaining.",
            )

        # Verification successful - execute state transition atomically
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order.id)
            old_status = order.status
            order.status = "PickedUp"
            order.pickup_code_attempts = 0
            order.pickup_verified_at = timezone.now()
            if not order.picked_up_at:
                order.picked_up_at = timezone.now()

            order.save(
                update_fields=[
                    "status",
                    "pickup_code_attempts",
                    "pickup_verified_at",
                    "picked_up_at",
                    "updated_at",
                ]
            )

        # Log order event
        order_event_signal.send(
            sender=self.__class__,
            order=order,
            event="Order Picked Up (V2 Verified)",
            description=f"Order picked up by rider {rider.rider_id} using verified pickup code",
            old_value=old_status,
            new_value="PickedUp",
            created_by=request.user,
        )

        # Send push notification to rider in background
        def _notify_pickup_success():
            try:
                notify_rider(
                    rider=rider,
                    title="Pickup Confirmed 📦",
                    body=f"Pickup verified for order #{order_number}. Safe travels to your destination!",
                    data={"order_number": order_number, "status": "PickedUp"},
                )
            except Exception as exc:
                logger.warning(f"Pickup notification failed: {exc}")

        threading.Thread(target=_notify_pickup_success, daemon=True).start()

        return service_response(
            status="success",
            message="Order picked up successfully.",
            data={
                "order_number": order_number,
                "status": "PickedUp",
                "picked_up_at": order.picked_up_at.isoformat() if order.picked_up_at else None,
            },
            status_code=200,
        )


class DeliveryCompleteV2View(APIView):
    """
    Rider marks an individual delivery stop as Delivered by providing the 6-digit drop code.
    POST /api/orders/v2/delivery/<delivery_id>/deliver/
    {
        "drop_code": "654321"
    }
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
    def post(self, request: Request, delivery_id: str) -> Response:
        serializer = DeliveryCompleteV2Serializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            first_err = next(iter(errors.values()))[0] if errors else "Invalid request data."
            raise ServiceException(status_code=400, message=str(first_err))

        drop_code = serializer.validated_data["drop_code"]

        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            raise ServiceException(status_code=403, message="Rider profile not found.")

        try:
            delivery = (
                Delivery.objects.select_related("order")
                .get(id=delivery_id)
            )
            order = delivery.order
        except (Delivery.DoesNotExist, ValueError):
            raise ServiceException(status_code=404, message="Delivery not found.")

        if order.rider_id != rider.id:
            raise ServiceException(
                status_code=403,
                message="You are not the assigned rider for this delivery.",
            )

        # Idempotent return if already delivered
        if delivery.status == "Delivered":
            return service_response(
                status="success",
                message="Delivery has already been completed.",
                data={
                    "delivery_id": str(delivery.id),
                    "status": "Delivered",
                    "order_status": order.status,
                },
                status_code=200,
            )

        if delivery.status in ["Failed", "Canceled"]:
            raise ServiceException(
                status_code=400,
                message=f"Cannot complete delivery in current status: {delivery.status}",
            )

        # Check max failed attempts on delivery
        if delivery.drop_code_attempts >= MAX_VERIFICATION_ATTEMPTS:
            raise ServiceException(
                status_code=400,
                message="Delivery verification is locked due to too many failed attempts (maximum 5). Please contact support.",
            )

        # Compare drop code
        if delivery.drop_code != drop_code:
            delivery.drop_code_attempts += 1
            delivery.save(update_fields=["drop_code_attempts"])
            remaining = MAX_VERIFICATION_ATTEMPTS - delivery.drop_code_attempts
            if remaining <= 0:
                raise ServiceException(
                    status_code=400,
                    message="Incorrect drop code. Verification is now locked after 5 failed attempts.",
                )
            raise ServiceException(
                status_code=400,
                message=f"Incorrect drop code. {remaining} attempt(s) remaining.",
            )

        # Verification successful - execute state transition atomically
        with transaction.atomic():
            delivery = Delivery.objects.select_for_update().get(id=delivery.id)
            order = Order.objects.select_for_update().get(id=delivery.order_id)
            old_delivery_status = delivery.status
            delivery.status = "Delivered"
            delivery.drop_code_attempts = 0
            delivery.delivered_at = timezone.now()
            delivery.drop_verified_at = timezone.now()
            delivery.save(
                update_fields=[
                    "status",
                    "drop_code_attempts",
                    "delivered_at",
                    "drop_verified_at",
                ]
            )

            # Check if all deliveries are now completed
            all_delivered = not order.deliveries.exclude(status="Delivered").exists()
            if all_delivered:
                _finalize_order_completion(order, rider, request.user)

        # Log delivery completed event
        order_event_signal.send(
            sender=self.__class__,
            order=order,
            event="Delivery Completed (V2 Verified)",
            description=f"Delivery to {delivery.receiver_name} completed by rider {rider.rider_id} using verified drop code",
            old_value=old_delivery_status,
            new_value="Delivered",
            created_by=request.user,
        )

        return service_response(
            status="success",
            message="Delivery completed successfully.",
            data={
                "delivery_id": str(delivery.id),
                "status": "Delivered",
                "delivered_at": delivery.delivered_at.isoformat() if delivery.delivered_at else None,
                "order_number": order.order_number,
                "order_status": order.status,
                "all_delivered": all_delivered,
            },
            status_code=200,
        )


class OrderCompleteV2View(APIView):
    """
    Rider marks single-delivery order (or order) as completed by providing the 6-digit drop code.
    POST /api/orders/v2/complete/
    {
        "order_number": "6158001",
        "drop_code": "654321"
    }
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
    def post(self, request: Request) -> Response:
        serializer = OrderCompleteV2Serializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            first_err = next(iter(errors.values()))[0] if errors else "Invalid request data."
            raise ServiceException(status_code=400, message=str(first_err))

        order_number = serializer.validated_data["order_number"]
        drop_code = serializer.validated_data["drop_code"]

        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            raise ServiceException(status_code=403, message="Rider profile not found.")

        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            raise ServiceException(status_code=404, message="Order not found.")

        if order.rider_id != rider.id:
            raise ServiceException(
                status_code=403,
                message="You are not the assigned rider for this order.",
            )

        # Idempotent return if already Done
        if order.status == "Done":
            return service_response(
                status="success",
                message="Order is already completed.",
                data={"order_number": order_number, "status": "Done"},
                status_code=200,
            )

        # For single delivery or finding delivery matching drop code or pending delivery
        deliveries = order.deliveries.exclude(status="Delivered")
        if not deliveries.exists():
            _finalize_order_completion(order, rider, request.user)
            return service_response(
                status="success",
                message="Order completed successfully.",
                data={"order_number": order_number, "status": "Done"},
                status_code=200,
            )

        # Locate target delivery: either single delivery, or find matching drop code
        target_delivery = deliveries.filter(drop_code=drop_code).first()
        if not target_delivery:
            # Use the next pending delivery for attempt tracking
            target_delivery = deliveries.first()

        if target_delivery.drop_code_attempts >= MAX_VERIFICATION_ATTEMPTS:
            raise ServiceException(
                status_code=400,
                message="Delivery verification is locked due to too many failed attempts (maximum 5). Please contact support.",
            )

        if target_delivery.drop_code != drop_code:
            target_delivery.drop_code_attempts += 1
            target_delivery.save(update_fields=["drop_code_attempts"])
            remaining = MAX_VERIFICATION_ATTEMPTS - target_delivery.drop_code_attempts
            if remaining <= 0:
                raise ServiceException(
                    status_code=400,
                    message="Incorrect drop code. Verification is now locked after 5 failed attempts.",
                )
            raise ServiceException(
                status_code=400,
                message=f"Incorrect drop code. {remaining} attempt(s) remaining.",
            )

        # Verification successful - execute state transition atomically
        with transaction.atomic():
            target_delivery = Delivery.objects.select_for_update().get(id=target_delivery.id)
            order = Order.objects.select_for_update().get(id=order.id)
            target_delivery.status = "Delivered"
            target_delivery.drop_code_attempts = 0
            target_delivery.delivered_at = timezone.now()
            target_delivery.drop_verified_at = timezone.now()
            target_delivery.save(
                update_fields=[
                    "status",
                    "drop_code_attempts",
                    "delivered_at",
                    "drop_verified_at",
                ]
            )

            all_delivered = not order.deliveries.exclude(status="Delivered").exists()
            if all_delivered:
                _finalize_order_completion(order, rider, request.user)

        # Log delivery completed event
        order_event_signal.send(
            sender=self.__class__,
            order=order,
            event="Order Completed (V2 Verified)",
            description=f"Order {order_number} delivery completed by rider {rider.rider_id} using verified drop code",
            old_value=order.status,
            new_value="Done" if all_delivered else order.status,
            created_by=request.user,
        )

        return service_response(
            status="success",
            message="Order delivery completed successfully." if all_delivered else "Delivery stop completed.",
            data={
                "order_number": order_number,
                "status": "Done" if all_delivered else order.status,
                "all_delivered": all_delivered,
            },
            status_code=200,
        )
