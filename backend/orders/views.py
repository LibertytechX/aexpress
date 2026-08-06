from orders.serializers import CreateParcelSerializer
from rest_framework.settings import api_settings
from dispatcher.authentication import MerchantAPIKeyAuthentication
from devs.models import ErrorLog
import traceback
from dispatcher.models import SystemSettings
import logging
import threading
from rest_framework import serializers, status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Order, Delivery, Vehicle, OrderEvent
from .signals import order_event_signal
from .utils import calculate_route
from .pricing import calculate_effective_fare
from .serializers import (
    OrderSerializer,
    VehicleSerializer,
    QuickSendSerializer,
    MultiDropSerializer,
    BulkImportSerializer,
    AssignedOrderSerializer,
    AssignedRouteSerializer,
    OrderCancelSerializer,
    OrderStatusUpdateSerializer,
    MergeGroupedOrdersSerializer,
)
from .permissions import IsRider
from dispatcher.models import Rider
from dispatcher.utils import emit_activity
from wallet.models import Wallet, Charge
from wallet.escrow import EscrowManager
from wallet.corebanking_service import create_virtual_account
from riders.notifications import notify_rider
from riders.models import RiderEarning, RiderCodRecord
from dispatcher.tasks import send_merchant_notification
from sparky_utils.response import service_response
from sparky_utils.advice import exception_advice
from sparky_utils.exceptions import ServiceException
from dispatcher.serializers import OrderEventSerializer
from subscriptions.services import (
    process_order_subscription,
    get_active_postpaid_subscription,
    accumulate_postpaid_order,
)
from .services import SmartPercelIntegration, get_order_service

logger = logging.getLogger(__name__)


class VehicleListView(APIView):
    """API endpoint to list all available vehicles."""

    authentication_classes = [
        MerchantAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all active vehicles with pricing, applying merchant overrides or manual price lists."""
        from .models import MerchantPricingOverride, MerchantPriceList

        vehicles = Vehicle.objects.filter(is_active=True)
        results = []

        for vehicle in vehicles:
            v_data = VehicleSerializer(vehicle).data
            v_data["has_manual_pricing"] = False
            v_data["manual_price_list"] = None

            # 1. Check for manual Price List (highest precedence)
            price_list = (
                MerchantPriceList.objects.filter(
                    merchant=request.user, vehicle=vehicle, is_active=True
                )
                .prefetch_related("items")
                .first()
            )

            if price_list:
                v_data["has_manual_pricing"] = True
                v_data["manual_price_list"] = {
                    "name": price_list.name,
                    "items": [
                        {
                            "label": item.label,
                            "min_km": float(item.min_km),
                            "max_km": float(item.max_km),
                            "fixed_fee": float(item.fixed_fee),
                        }
                        for item in price_list.items.all()
                    ],
                }
                # For manual lists, we nullify standard rates to avoid confusion
                v_data["base_fare"] = 0.0
                v_data["rate_per_km"] = 0.0
                v_data["rate_per_minute"] = 0.0
                v_data["pricing_tiers"] = None
            else:
                # 2. Check for traditional merchant override
                override = MerchantPricingOverride.objects.filter(
                    merchant=request.user, vehicle=vehicle, is_active=True
                ).first()

                if override:
                    if override.flat_fee is not None:
                        v_data["base_fare"] = float(override.flat_fee)
                        v_data["rate_per_km"] = 0.0
                        v_data["rate_per_minute"] = 0.0
                        v_data["pricing_tiers"] = None
                    elif override.pricing_tiers:
                        v_data["pricing_tiers"] = override.pricing_tiers

            results.append(v_data)

        return Response(
            {"success": True, "vehicles": results}, status=status.HTTP_200_OK
        )


class VehicleUpdateView(generics.UpdateAPIView):
    """API endpoint to update vehicle pricing."""

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        """Update vehicle details."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {
                "success": True,
                "message": f"Vehicle {instance.name} updated successfully",
                "vehicle": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class QuickSendView(APIView):
    """API endpoint for Quick Send order creation."""

    authentication_classes = [
        MerchantAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]

    permission_classes = [permissions.IsAuthenticated]

    # TODO Refactor to be less complex

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        """Create a Quick Send order with single delivery."""
        from django.utils import timezone
        from datetime import timedelta

        order_service = get_order_service()

        # Get requested mode (defaults to quick)
        requested_mode = request.data.get("mode", "quick")
        if requested_mode not in ["quick", "grouped"]:
            requested_mode = "quick"

        one_minute_ago = timezone.now() - timedelta(minutes=1)
        if Order.objects.filter(
            user=request.user, mode=requested_mode, created_at__gte=one_minute_ago
        ).exists():
            return Response(
                {
                    "success": False,
                    "errors": {
                        "non_field_errors": [
                            f"Please wait a minute before creating another {requested_mode.replace('_', ' ').title()} order."
                        ]
                    },
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = QuickSendSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # ------------------------------------------------------------------
        # SmartParcel Integration (Pre-Creation)
        # ------------------------------------------------------------------
        is_pickup_percel = data.get("is_pickup_percel", False)
        isdelivery_percel = data.get("isdelivery_percel", False)
        is_percel_order = is_pickup_percel or isdelivery_percel
        percel_info = None
        percel_payload = {
            "sendername": data.get("sender_name", ""),
            "senderphone": data.get("sender_phone", ""),
            "senderemail": request.user.email,
            "recipientname": data.get("receiver_name", ""),
            "recipientphone": data.get("receiver_phone", ""),
            "recipientemail": request.user.email,
            "boxid": data.get("box_id", ""),
            "sizeid": data.get("locker_size_id", ""),
            "parceldescription": data.get("notes", "Parcel Delivery"),
            "parcelvalue": 0,  # default placeholder
        }
        ok, response = order_service.process_parcel_delivery(
            is_pickup_percel, isdelivery_percel, data, percel_payload
        )

        if not ok:
            raise ServiceException(
                status_code=response.get("status_code"), message=response.get("message")
            )

        # Explicitly update addresses from response
        data["pickup_address"] = response.get("pickup_address", data["pickup_address"])
        data["dropoff_address"] = response.get(
            "dropoff_address", data["dropoff_address"]
        )
        percel_info = response.get("parcel_info")
        # Get vehicle
        vehicle = Vehicle.objects.get(name=data["vehicle"], is_active=True)

        # Calculate total amount using effective fare (handles overrides)
        distance_km = data.get("distance_km", 0)
        duration_minutes = data.get("duration_minutes", 0)
        total_amount = calculate_effective_fare(
            request.user, vehicle, distance_km, duration_minutes
        )

        # Apply 30% discount for grouped orders
        if data.get("mode") == "grouped":
            if (
                not hasattr(request.user, "merchant_profile")
                or not request.user.merchant_profile.can_group_orders
            ):
                return Response(
                    {
                        "success": False,
                        "errors": {
                            "non_field_errors": [
                                "You are not allowed to create grouped orders."
                            ]
                        },
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            from decimal import Decimal

            total_amount = (total_amount * Decimal("0.7")).quantize(Decimal("0.01"))

        # Create order
        order = Order.objects.create(
            user=request.user,
            mode=data.get("mode", "quick"),
            vehicle=vehicle,
            pickup_address=data["pickup_address"],
            sender_name=data["sender_name"],
            sender_phone=data["sender_phone"],
            payment_method=data["payment_method"],
            total_amount=total_amount,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            notes=data.get("notes", ""),
            scheduled_pickup_time=data.get("scheduled_pickup_time"),
            collect_on_delivery=data.get("collect_on_delivery", False),
            cod_amount=data.get("cod_amount"),
            is_percel_order=is_percel_order,
            is_pickup_percel=is_pickup_percel,
            isdelivery_percel=isdelivery_percel,
            percel_info=percel_info,
        )
        payment_method = data.get("payment_method", "wallet")
        ok, response = order_service.process_non_cash_payment(
            payment_method, request.user, order
        )

        if not ok:
            return Response(
                {
                    "success": False,
                    "errors": {"non_field_errors": [response.get("message")]},
                },
                status=response.get("status_code", status.HTTP_400_BAD_REQUEST),
            )

        # Create single delivery
        Delivery.objects.create(
            order=order,
            pickup_address=data["pickup_address"],
            pickup_latitude=order.pickup_latitude,
            pickup_longitude=order.pickup_longitude,
            sender_name=data["sender_name"],
            sender_phone=data["sender_phone"],
            dropoff_address=data["dropoff_address"],
            receiver_name=data["receiver_name"],
            receiver_phone=data["receiver_phone"],
            package_type=data.get("package_type", "Box"),
            notes=data.get("notes", ""),
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            sequence=1,
            cod_amount=data.get("cod_amount") or 0,
        )

        # Store the resulting parcel JSON (containing tracking number etc)
        order.percel_info = percel_info
        order.save()

        # Emit activity event for live feed (fire-and-forget in background thread)
        merchant_name = (
            getattr(request.user, "business_name", None)
            or getattr(request.user, "contact_name", None)
            or "Unknown"
        )
        threading.Thread(
            target=emit_activity,
            kwargs={
                "event_type": "new_order",
                "order_id": order.order_number,
                "text": f"New order {order.order_number} from {merchant_name}",
                "color": "gold",
                "metadata": {
                    "merchant": merchant_name,
                    "amount": str(total_amount),
                    "pickup": data["pickup_address"],
                    "dropoff": data["dropoff_address"],
                },
            },
            daemon=True,
        ).start()

        # Notify all online riders about the new order (fire-and-forget in background)
        def _notify_riders():
            try:
                online_riders = Rider.objects.filter(
                    status=Rider.Status.ONLINE, is_active=True, is_authorized=True
                )
                for rider in online_riders:
                    notify_rider(
                        rider=rider,
                        title="New Order Available",
                        body=f"Quick Send pickup from {order.pickup_address}",
                        data={"order_number": order.order_number, "mode": "quick"},
                    )
            except Exception as e:
                logger.warning(f"Failed to send new-order notifications: {e}")

        threading.Thread(target=_notify_riders, daemon=True).start()
        order_serializer = OrderSerializer(order)

        # Trigger order-created webhook in background
        def _trigger_created():
            try:
                from webhooks.utils import trigger_webhook

                payload = {
                    "event": "order-created",
                    "timestamp": order.created_at.isoformat(),
                    "data": order_serializer.data,
                }
                user = request.user
                if user.is_merchant:
                    merchant_profile = user.merchant_profile
                    trigger_webhook("order-created", payload, merchant_profile)
            except Exception as e:
                logger.error(f"Failed to trigger order-created webhook: {e}")

        threading.Thread(target=_trigger_created, daemon=True).start()

        if payment_method in ["cash", "cash_on_pickup", "receiver_pays"]:
            from .tasks import create_order_charge

            create_order_charge.delay(order.id)

        return Response(
            {
                "success": True,
                "message": "Quick Send order created successfully!",
                "order": order_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class MultiDropView(APIView):
    """API endpoint for Multi-Drop order creation."""

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        """Create a Multi-Drop order with multiple deliveries."""
        from django.utils import timezone
        from datetime import timedelta

        order_service = get_order_service()

        # whitelist = ["https://send.axpress.net/", "https://move.axpress.net/"]

        one_minute_ago = timezone.now() - timedelta(minutes=1)
        if Order.objects.filter(
            user=request.user, mode="multi", created_at__gte=one_minute_ago
        ).exists():
            return Response(
                {
                    "success": False,
                    "errors": {
                        "non_field_errors": [
                            "Please wait a minute before creating another Multi-Drop order."
                        ]
                    },
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = MultiDropSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # Get vehicle
        vehicle = Vehicle.objects.get(name=data["vehicle"], is_active=True)

        # Calculate total amount using effective fare (handles overrides)
        num_deliveries = len(data["deliveries"])
        distance_km = data.get("distance_km", 0)
        duration_minutes = data.get("duration_minutes", 0)
        unit_fare = calculate_effective_fare(
            request.user, vehicle, distance_km, duration_minutes
        )
        total_amount = unit_fare

        # Create order
        order = Order.objects.create(
            user=request.user,
            mode="multi",
            vehicle=vehicle,
            pickup_address=data["pickup_address"],
            sender_name=data["sender_name"],
            sender_phone=data["sender_phone"],
            payment_method=data["payment_method"],
            total_amount=total_amount,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            notes=data.get("notes", ""),
            scheduled_pickup_time=data.get("scheduled_pickup_time"),
            collect_on_delivery=data.get("collect_on_delivery", False),
        )
        # get the payment method
        payment_method = data.get("payment_method", "wallet")
        user = request.user
        ok, response = order_service.process_non_cash_payment(
            payment_method, user, order
        )
        if not ok:
            return Response(
                {
                    "success": False,
                    "errors": {"non_field_errors": [response.get("message")]},
                },
                status=response.get("status_code", status.HTTP_400_BAD_REQUEST),
            )
        # Create multiple deliveries
        for idx, delivery_data in enumerate(data["deliveries"], start=1):
            Delivery.objects.create(
                order=order,
                pickup_address=data["pickup_address"],
                pickup_latitude=order.pickup_latitude,
                pickup_longitude=order.pickup_longitude,
                sender_name=data["sender_name"],
                sender_phone=data["sender_phone"],
                dropoff_address=delivery_data["dropoff_address"],
                receiver_name=delivery_data["receiver_name"],
                receiver_phone=delivery_data["receiver_phone"],
                package_type=delivery_data.get("package_type", "Box"),
                notes=delivery_data.get("notes", ""),
                cod_amount=delivery_data.get("cod_amount", 0),
                distance_km=delivery_data.get("distance_km"),
                duration_minutes=delivery_data.get("duration_minutes"),
                sequence=idx,
            )

        # Notify all online riders about the new order (fire-and-forget in background)
        def _notify_riders_multi():
            try:
                online_riders = Rider.objects.filter(
                    status=Rider.Status.ONLINE, is_active=True, is_authorized=True
                )
                for rider in online_riders:
                    notify_rider(
                        rider=rider,
                        title="New Order Available",
                        body=f"Multi-Drop ({num_deliveries} stops) pickup from {order.pickup_address}",
                        data={"order_number": order.order_number, "mode": "multi"},
                    )
            except Exception as e:
                logger.warning(f"Failed to send new-order notifications: {e}")

        threading.Thread(target=_notify_riders_multi, daemon=True).start()

        order_serializer = OrderSerializer(order)

        # Trigger order-created webhook in background
        def _trigger_multi_created():
            try:
                from webhooks.utils import trigger_webhook

                payload = {
                    "event": "order-created",
                    "timestamp": order.created_at.isoformat(),
                    "data": order_serializer.data,
                }
                trigger_webhook("order-created", payload)
            except Exception as e:
                logger.error(f"Failed to trigger order-created webhook: {e}")

        threading.Thread(target=_trigger_multi_created, daemon=True).start()

        if data.get("payment_method") in ["cash", "cash_on_pickup", "receiver_pays"]:
            from .tasks import create_order_charge

            create_order_charge.delay(order.id)

        return Response(
            {
                "success": True,
                "message": f"Multi-Drop order created with {num_deliveries} deliveries!",
                "order": order_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class BulkImportView(APIView):
    """API endpoint for Bulk Import order creation."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Create a Bulk Import order with multiple deliveries."""
        from django.utils import timezone
        from datetime import timedelta

        order_service = get_order_service()

        one_minute_ago = timezone.now() - timedelta(minutes=1)
        if Order.objects.filter(
            user=request.user, mode="bulk", created_at__gte=one_minute_ago
        ).exists():
            return Response(
                {
                    "success": False,
                    "errors": {
                        "non_field_errors": [
                            "Please wait a minute before creating another Bulk Import order."
                        ]
                    },
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = BulkImportSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # Get vehicle
        vehicle = Vehicle.objects.get(name=data["vehicle"], is_active=True)

        # Calculate total amount using effective fare (handles overrides)
        num_deliveries = len(data["deliveries"])
        distance_km = data.get("distance_km", 0)
        duration_minutes = data.get("duration_minutes", 0)
        unit_fare = calculate_effective_fare(
            request.user, vehicle, distance_km, duration_minutes
        )
        total_amount = unit_fare * num_deliveries

        # Create order
        order = Order.objects.create(
            user=request.user,
            mode="bulk",
            vehicle=vehicle,
            pickup_address=data["pickup_address"],
            sender_name=data["sender_name"],
            sender_phone=data["sender_phone"],
            payment_method=data["payment_method"],
            total_amount=total_amount,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            notes=data.get("notes", ""),
            scheduled_pickup_time=data.get("scheduled_pickup_time"),
            collect_on_delivery=data.get("collect_on_delivery", False),
        )

        payment_method = data.get("payment_method", "wallet")
        user = request.user
        ok, response = order_service.process_non_cash_payment(
            payment_method, user, order
        )
        if not ok:
            return Response(
                {
                    "success": False,
                    "errors": {"non_field_errors": [response.get("message")]},
                },
                status=response.get("status_code", status.HTTP_400_BAD_REQUEST),
            )
        # Create multiple deliveries
        for idx, delivery_data in enumerate(data["deliveries"], start=1):
            Delivery.objects.create(
                order=order,
                pickup_address=data["pickup_address"],
                pickup_latitude=order.pickup_latitude,
                pickup_longitude=order.pickup_longitude,
                sender_name=data["sender_name"],
                sender_phone=data["sender_phone"],
                dropoff_address=delivery_data["dropoff_address"],
                receiver_name=delivery_data["receiver_name"],
                receiver_phone=delivery_data["receiver_phone"],
                package_type=delivery_data.get("package_type", "Box"),
                notes=delivery_data.get("notes", ""),
                cod_amount=delivery_data.get("cod_amount", 0),
                distance_km=delivery_data.get("distance_km"),
                duration_minutes=delivery_data.get("duration_minutes"),
                sequence=idx,
            )

        # Notify all online riders about the new order (fire-and-forget in background)
        def _notify_riders_bulk():
            try:
                online_riders = Rider.objects.filter(
                    status=Rider.Status.ONLINE, is_active=True, is_authorized=True
                )
                for rider in online_riders:
                    notify_rider(
                        rider=rider,
                        title="New Order Available",
                        body=f"Bulk Import ({num_deliveries} stops) pickup from {order.pickup_address}",
                        data={"order_number": order.order_number, "mode": "bulk"},
                    )
            except Exception as e:
                logger.warning(f"Failed to send new-order notifications: {e}")

        threading.Thread(target=_notify_riders_bulk, daemon=True).start()

        order_serializer = OrderSerializer(order)
        # Trigger order-created webhook in background

        def _trigger_bulk_created():
            try:
                from webhooks.utils import trigger_webhook

                payload = {
                    "event": "order-created",
                    "timestamp": order.created_at.isoformat(),
                    "data": order_serializer.data,
                }
                trigger_webhook("order-created", payload)
            except Exception as e:
                logger.error(f"Failed to trigger order-created webhook: {e}")

        threading.Thread(target=_trigger_bulk_created, daemon=True).start()

        if data.get("payment_method") in ["cash", "cash_on_pickup", "receiver_pays"]:
            from .tasks import create_order_charge

            create_order_charge.delay(order.id)

        return Response(
            {
                "success": True,
                "message": f"Bulk Import order created with {num_deliveries} deliveries!",
                "order": order_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class OrderPayNowView(APIView):
    """
    API endpoint to initiate the 'Pay Now' flow for an order.
    - Retrieves or creates the user's virtual account.
    - Populates the order's payment_info field.
    - Creates a pending Charge record in the wallet app.
    """

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response(
                {"success": False, "message": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # if order.payment_status == "Paid":
        #     return Response(
        #         {"success": False, "message": "Order is already paid."},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )

        # Get or create virtual account
        try:
            virtual_account = create_virtual_account(order.user)
            order.payment_info = {
                "account_number": virtual_account.account_number,
                "account_name": virtual_account.account_name,
                "bank_name": virtual_account.bank_name,
                "bank_code": virtual_account.bank_code,
            }
            order.save(update_fields=["payment_info"])
        except Exception as e:
            logger.error(f"Failed to create virtual account for pay-now: {e}")
            return Response(
                {
                    "success": False,
                    "message": "Failed to generate payment information.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Create or update pending charge
        charge, created = Charge.objects.get_or_create(
            user=order.user,
            order=order,
            defaults={"amount": order.total_amount, "status": "pending"},
        )
        if not created:
            charge.amount = order.total_amount
            charge.status = "pending"
            charge.save()

        return Response(
            {
                "success": True,
                "message": "Payment information generated. Please transfer the total amount to the virtual account provided.",
                "payment_info": order.payment_info,
                "total_amount": str(order.total_amount),
            },
            status=status.HTTP_200_OK,
        )


class OrderListView(APIView):
    """API endpoint to list all orders for the authenticated user."""

    authentication_classes = [
        MerchantAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all orders for the current user with optional filtering."""
        # Get query parameters
        status_filter = request.query_params.get("status", None)
        mode_filter = request.query_params.get("mode", None)
        limit = request.query_params.get("limit", None)

        # Base queryset
        orders = (
            Order.objects.filter(user=request.user)
            .select_related("vehicle", "rider", "rider__user")
            .prefetch_related("deliveries")
        )

        # Apply filters
        if status_filter:
            orders = orders.filter(status=status_filter)

        if mode_filter:
            orders = orders.filter(mode=mode_filter)

        # Apply limit
        if limit:
            try:
                orders = orders[: int(limit)]
            except ValueError:
                pass

        # Serialize
        serializer = OrderSerializer(orders, many=True)

        return Response(
            {"success": True, "count": len(serializer.data), "orders": serializer.data},
            status=status.HTTP_200_OK,
        )


class OrderEventAPIView(APIView):
    """
    Order Event API View for listing the events for a particular order
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice()
    def get(self, request, *args, **kwargs):
        order_number = kwargs.get("order_number")
        order = Order.objects.get(order_number=order_number)
        events_queryset = order.events.all().order_by("-created_at")
        serializer = OrderEventSerializer(events_queryset, many=True)

        return service_response(
            status="success",
            message="Order events retrieved successfully",
            data=serializer.data,
            status_code=200,
        )


class OrderDetailView(APIView):
    """API endpoint to get details of a specific order."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_number):
        """Get order details by order number."""
        try:
            order = (
                Order.objects.select_related("vehicle", "rider", "rider__user")
                .prefetch_related("deliveries")
                .get(order_number=order_number, user=request.user)
            )
        except Order.DoesNotExist:
            return Response(
                {"success": False, "message": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OrderSerializer(order)

        return Response(
            {"success": True, "order": serializer.data}, status=status.HTTP_200_OK
        )


class OrderStatsView(APIView):
    """API endpoint to get order statistics for the dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get order statistics for the current user."""
        orders = Order.objects.filter(user=request.user)

        # Calculate stats
        total_orders = orders.count()
        pending_orders = orders.filter(
            status__in=["Pending", "Assigned", "Started"]
        ).count()
        completed_orders = orders.filter(status="Done").count()
        canceled_orders = orders.filter(
            status__in=["CustomerCanceled", "RiderCanceled"]
        ).count()

        # Calculate total spent (only completed orders)
        total_spent = sum(
            float(order.total_amount) for order in orders.filter(status="Done")
        )

        # Average delivery cost
        avg_cost = total_spent / completed_orders if completed_orders > 0 else 0

        return Response(
            {
                "success": True,
                "stats": {
                    "total_orders": total_orders,
                    "pending_orders": pending_orders,
                    "completed_orders": completed_orders,
                    "canceled_orders": canceled_orders,
                    "total_spent": round(total_spent, 2),
                    "average_cost": round(avg_cost, 2),
                },
            },
            status=status.HTTP_200_OK,
        )


class CalculateFareView(APIView):
    """
    API endpoint to calculate fare based on vehicle, distance and duration.

    POST /api/orders/calculate-fare/
    {
        "vehicle": "Bike",
        "distance_km": 5.2,
        "duration_minutes": 15
    }
    """

    authentication_classes = [
        MerchantAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        vehicle_name = request.data.get("vehicle")
        distance_km = request.data.get("distance_km")
        duration_minutes = request.data.get("duration_minutes")

        if not all(
            [vehicle_name, distance_km is not None, duration_minutes is not None]
        ):
            return Response(
                {
                    "success": False,
                    "error": "Missing required fields: vehicle, distance_km, duration_minutes",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            vehicle = Vehicle.objects.get(name__iexact=vehicle_name, is_active=True)
        except Vehicle.DoesNotExist:
            return Response(
                {"success": False, "error": f"Vehicle {vehicle_name} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            pricing_data = calculate_effective_fare(
                request.user,
                vehicle,
                float(distance_km),
                int(duration_minutes),
                return_metadata=True,
            )
            total_amount = pricing_data["fare"]
            source = pricing_data["source"]
            label = pricing_data["label"]

            response_data = {
                "success": True,
                "price": total_amount,
                "pricing_source": source,
                "pricing_label": label,
            }

            if source == "manual_list":
                response_data["breakdown"] = {
                    "type": "Manual Price List",
                    "description": f"Fixed rate for range matching '{label}'",
                }
            else:
                response_data["breakdown"] = {
                    "base_fare": vehicle.base_fare,
                    "distance_cost": float(distance_km) * float(vehicle.rate_per_km),
                    "time_cost": int(duration_minutes) * float(vehicle.rate_per_minute),
                }

            return Response(response_data, status=status.HTTP_200_OK)

        except (ValueError, TypeError) as e:
            return Response(
                {"success": False, "error": f"Invalid data format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BulkCalculateFareView(APIView):
    """
    API endpoint to calculate fare based on coordinates and order mode for all vehicles.

    POST /api/orders/bulk-calculate-fare/
    {
        "mode": "quick", // quick, multi, or bulk
        "pickup": {"lat": 3.33, "long": 34.99},
        "deliveries": [{"lat": 32.32, "long": 23.53}]
    }
    """

    authentication_classes = [
        MerchantAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        mode = request.data.get("mode", "quick")
        pickup = request.data.get("pickup")
        deliveries = request.data.get("deliveries", [])
        if isinstance(pickup, str) or isinstance(deliveries, str):
            return Response(
                {
                    "success": False,
                    "error": "Invalid data format: pickup and deliveries must be dictionaries",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not pickup or not deliveries:
            return Response(
                {
                    "success": False,
                    "error": "Missing required fields: pickup and deliveries",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        vehicles = Vehicle.objects.filter(is_active=True)
        results = {}

        try:
            if mode == "quick":
                route_data = calculate_route(origin=pickup, destinations=deliveries)
                if not route_data:
                    return Response(
                        {"success": False, "error": "Could not calculate route"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                dist_km = route_data["distance_km"]
                dur_mins = route_data["duration_minutes"]

                for vehicle in vehicles:
                    fare = calculate_effective_fare(
                        request.user, vehicle, dist_km, dur_mins
                    )
                    results[vehicle.name] = {
                        "price": fare,
                        "distance_km": dist_km,
                        "duration_minutes": dur_mins,
                    }

            elif mode in ["multi", "bulk"]:
                total_distances = 0
                total_durations = 0
                drop_fares = {v.name: 0 for v in vehicles}
                drop_details = []

                for idx, drop in enumerate(deliveries):
                    if idx == 0:
                        origin = pickup
                    else:
                        origin = deliveries[idx - 1]
                    route_data = calculate_route(origin=origin, destinations=[drop])
                    if not route_data:
                        continue

                    dist_km = route_data["distance_km"]
                    dur_mins = route_data["duration_minutes"]
                    total_distances += dist_km
                    total_durations += dur_mins

                    drop_info = {
                        "distance_km": dist_km,
                        "duration_minutes": dur_mins,
                        "fares": {},
                    }
                    # fix this
                    for vehicle in vehicles:
                        fare = calculate_effective_fare(
                            request.user, vehicle, dist_km, dur_mins
                        )
                        drop_fares[vehicle.name] += fare
                        drop_info["fares"][vehicle.name] = fare
                    drop_details.append(drop_info)
                # for vehicle in vehicles:
                #     fare = calculate_effective_fare(
                #         request.user, vehicle, total_distances, total_durations
                #     )
                #     drop_fares[vehicle.name] = fare
                #     # drop_info["fares"][vehicle.name] = fare
                # # drop_details.append(drop_info)

                if not drop_details:
                    return Response(
                        {
                            "success": False,
                            "error": "Could not calculate route for any delivery",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                for vehicle in vehicles:
                    results[vehicle.name] = {
                        "price": drop_fares[vehicle.name],
                        "distance_km": round(total_distances, 2),
                        "duration_minutes": total_durations,
                        "drop_details": drop_details,
                    }

            return Response(
                {"success": True, "mode": mode, "vehicles": results},
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CancelOrderView(APIView):
    """
    Cancel an order and refund escrowed funds if applicable.

    POST /api/orders/cancel/{order_number}/
    {
        "reason": "Customer requested cancellation"
    }
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request, order_number):
        """Cancel an order and process refund if needed"""

        # Get cancellation reason
        reason = request.data.get("reason", "Order canceled by merchant")

        # Get the order
        try:
            order = Order.objects.get(order_number=order_number, user=request.user)
        except Order.DoesNotExist:
            raise ServiceException(
                status_code=404, message=f"Order {order_number} not found"
            )

        # Check if order can be canceled
        if order.status in ["Canceled", "CustomerCanceled"]:
            raise ServiceException(status_code=400, message="Order is already canceled")

        if order.status == "Delivered":
            raise ServiceException(
                status_code=400, message="Cannot cancel a delivered order"
            )

        # Once the package has been picked up, cancellation is not allowed
        if order.status in ["PickedUp", "Started"]:
            raise ServiceException(
                status_code=400,
                message="Cannot cancel an order that has already been picked up",
            )

        # Check if escrow was released (delivery completed)
        if order.escrow_held and order.escrow_released:
            raise ServiceException(
                status_code=400,
                message="Cannot cancel order - delivery already completed and funds released",
            )

        # Process escrow refund if applicable
        refund_processed = False
        refund_amount = 0

        if (
            order.payment_method == "wallet"
            and order.escrow_held
            and not order.escrow_released
        ):
            try:
                # Refund the escrowed funds
                escrow_transaction, refund_transaction = EscrowManager.refund_funds(
                    order_number=order.order_number, reason=reason
                )

                refund_processed = True
                refund_amount = float(refund_transaction.amount)

            except ValueError as e:
                raise ServiceException(
                    status_code=400, message=f"Failed to process refund: {str(e)}"
                )

        # Update order status
        old_status = order.status
        order.status = "CustomerCanceled"
        order.cancellation_reason = reason
        order.canceled_at = timezone.now()
        order.updated_at = timezone.now()
        order.save()

        # Cancel related charges
        charges = order.charges.filter(status__in=["pending", "failed"])
        for charge in charges:
            charge.status = "canceled"
            charge.save()

        # Trigger order-cancelled webhook in background
        def _trigger_cancelled():
            try:
                from webhooks.utils import trigger_webhook
                from .serializers import OrderSerializer

                payload = {
                    "event": "order-cancelled",
                    "timestamp": order.updated_at.isoformat(),
                    "data": OrderSerializer(order).data,
                    "reason": reason,
                }
                trigger_webhook("order-cancelled", payload)
            except Exception as e:
                logger.error(f"Failed to trigger order-cancelled webhook: {e}")

        threading.Thread(target=_trigger_cancelled, daemon=True).start()

        # Emit live-feed activity event for the dispatcher
        merchant_name = (
            getattr(request.user, "business_name", None)
            or getattr(request.user, "contact_name", None)
            or "Unknown"
        )
        emit_activity(
            event_type="cancelled",
            order_id=order.order_number,
            text=f"Order {order.order_number} cancelled by {merchant_name}",
            color="red",
            metadata={
                "merchant": merchant_name,
                "reason": reason,
                "old_status": old_status,
            },
        )

        # Notify the merchant that their order was cancelled
        try:
            merchant_profile = getattr(order.merchant, "merchant_profile", None)
            if merchant_profile:
                send_merchant_notification.delay(
                    merchant_id=str(merchant_profile.id),
                    title="Order Cancelled",
                    body=f"Your order #{order_number} has been cancelled.",
                    data={"order_number": order_number, "status": "CustomerCanceled"},
                    category="order_cancelled",
                )
        except Exception as exc:
            logger.warning(f"Merchant cancellation notification failed: {exc}")

        # Prepare response
        response_data = {
            "order": {
                "order_number": order.order_number,
                "old_status": old_status,
                "new_status": order.status,
                "payment_method": order.payment_method,
                "total_amount": float(order.total_amount),
                "canceled_at": order.updated_at.isoformat(),
            },
            "refund": {
                "processed": refund_processed,
                "amount": refund_amount,
                "reason": reason if refund_processed else None,
            },
        }

        return service_response(
            status="success",
            message=f"Order {order_number} has been canceled",
            data=response_data,
            status_code=200,
        )


class CancelableOrdersView(APIView):
    """
    Get list of orders that can be canceled.

    GET /api/orders/cancelable/
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all cancelable orders for the current user"""

        # Orders that can be canceled: not Delivered and not already Canceled
        cancelable_orders = (
            Order.objects.filter(user=request.user)
            .exclude(status__in=["Delivered", "Canceled"])
            .order_by("-created_at")
        )

        orders_data = []
        for order in cancelable_orders:
            orders_data.append(
                {
                    "order_number": order.order_number,
                    "status": order.status,
                    "payment_method": order.payment_method,
                    "total_amount": float(order.total_amount),
                    "created_at": order.created_at.isoformat(),
                    "can_refund": order.escrow_held and not order.escrow_released,
                    "escrow_held": order.escrow_held,
                    "escrow_released": order.escrow_released,
                }
            )

        return Response(
            {"count": len(orders_data), "orders": orders_data},
            status=status.HTTP_200_OK,
        )


class AssignedOrdersView(APIView):
    """
    Get list of orders assigned to the authenticated rider.
    Excludes certain terminal/canceled statuses.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        excluded_statuses = ["Done", "CustomerCanceled", "RiderCanceled", "Failed"]

        # Get rider profile
        rider_profile = getattr(request.user, "rider_profile", None)
        if not rider_profile:
            return Response(
                {"success": False, "message": "Authenticated user is not a driver."},
                status=status.HTTP_403_FORBIDDEN,
            )

        orders = (
            Order.objects.filter(rider=rider_profile)
            .exclude(status__in=excluded_statuses)
            .select_related("vehicle", "user")
            .prefetch_related("deliveries", "rider_offers")
            .order_by("-created_at")
        )

        serializer = AssignedOrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


def _advance_order(request, order_number, new_status, event_desc):
    """Helper to advance order status with validation."""
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    ser = OrderStatusUpdateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    # Proximity check for pickup actions
    if new_status in ["PickedUp", "Fulfilling"]:
        # let's just use the rider's known location instead
        # lat = ser.validated_data.get("latitude")
        # lng = ser.validated_data.get("longitude")
        lat = request.user.rider_profile.current_latitude
        lng = request.user.rider_profile.current_longitude

        if lat is None or lng is None:
            return service_response(
                status="error",
                message="Latitude and longitude are required to mark order as picked up.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure types are float for distance calculation
        lat, lng = float(lat), float(lng)

        if order.pickup_latitude is not None and order.pickup_longitude is not None:
            origin = {"lat": lat, "lng": lng}
            drop = {
                "lat": float(order.pickup_latitude),
                "lng": float(order.pickup_longitude),
            }
            route_data = calculate_route(origin=origin, destinations=[drop])

            if route_data:
                dist = float(route_data["distance_km"])
            else:
                from dispatcher.models import Zone

                dist = Zone.haversine_distance(
                    lat, lng, order.pickup_latitude, order.pickup_longitude
                )

            if dist > 2.0:  # 2000 meters
                return service_response(
                    status="error",
                    message=f"You are too far from the pickup location ({dist:.2f}km). Please move closer.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

    old_status = order.status
    order.status = new_status
    if new_status in ["PickedUp", "Fulfilling"] and not order.picked_up_at:
        order.picked_up_at = timezone.now()
    elif new_status == "Arrived" and not order.arrived_at:
        order.arrived_at = timezone.now()
    elif new_status == "Done" and not order.completed_at:
        order.completed_at = timezone.now()

    update_fields = ["status", "updated_at"]
    if order.picked_up_at:
        update_fields.append("picked_up_at")
    if order.arrived_at:
        update_fields.append("arrived_at")
    if order.completed_at:
        update_fields.append("completed_at")

    order.save(update_fields=update_fields)

    # Trigger order-completed webhook in background if status is Done
    if new_status == "Done":

        def _trigger_completed():
            try:
                from webhooks.utils import trigger_webhook
                from .serializers import OrderSerializer

                payload = {
                    "event": "order-completed",
                    "timestamp": (
                        order.completed_at.isoformat()
                        if order.completed_at
                        else timezone.now().isoformat()
                    ),
                    "data": OrderSerializer(order).data,
                }
                trigger_webhook("order-completed", payload)
            except Exception as e:
                logger.error(
                    f"Failed to trigger order-completed webhook in _advance_order: {e}"
                )

        threading.Thread(target=_trigger_completed, daemon=True).start()

    # Update rider location if provided
    rider_profile = getattr(request.user, "rider_profile", None)
    if rider_profile and ser.validated_data.get("latitude"):
        rider_profile.current_latitude = ser.validated_data["latitude"]
        rider_profile.current_longitude = ser.validated_data["longitude"]
        rider_profile.last_location_update = timezone.now()
        rider_profile.save(
            update_fields=[
                "current_latitude",
                "current_longitude",
                "last_location_update",
            ]
        )

    return Response({"status": new_status, "previous": old_status})



class OrderPickupView(APIView):
    """
    Endpoint for riders to mark an order as picked up.
    POST /api/orders/pickup/
    {
        "order_number": "6158001",
        "latitude": 6.45,
        "longitude": 3.39
    }
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        order_number = request.data.get("order_number")
        if not order_number:
            return service_response(
                status="error",
                message="order_number is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return _advance_order(request, order_number, "PickedUp", "Order Picked Up")


class OrderStartView(APIView):
    """
    Endpoint for riders to mark an order as started (trip to pickup).
    POST /api/orders/start/
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        order_number = request.data.get("order_number")
        if not order_number:
            return service_response(
                status="error",
                message="order_number is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        # TODO: check if the rider is assigned to this order

        response = _advance_order(request, order_number, "Started", "Order Started")

        # Push notification — fire-and-forget, don't block the response
        rider = getattr(request.user, "rider_profile", None)
        if rider:

            def _notify_rider_start():
                try:
                    notify_rider(
                        rider=rider,
                        title="Trip Started 🚀",
                        body=f"You're on your way to pick up order #{order_number}.",
                        data={"order_number": order_number, "status": "Started"},
                    )
                except Exception as exc:
                    logger.warning(f"Start notification failed: {exc}")

            threading.Thread(target=_notify_rider_start, daemon=True).start()

        return response


class OrderArrivedView(APIView):
    """
    Endpoint for riders to mark themselves as arrived at pickup.
    POST /api/orders/arrived/
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        order_number = request.data.get("order_number")
        if not order_number:
            return Response(
                {"error": "order_number is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return _advance_order(
            request, order_number, "Arrived", "Rider Arrived at Pickup"
        )


class OrderStatusChangeView(APIView):
    """
    Consolidated endpoint for riders to change order status.
    POST /api/orders/status/
    """

    # TODO: Add validation to check if the rider is assigned to this order
    # TODO: Add validation to check if the order is in the correct status to be updated

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        order_number = request.data.get("order_number")
        action = request.data.get("action")

        if not order_number or not action:
            return Response(
                {"error": "order_number and action are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        action = str(action).lower()

        if action == "start":
            response = _advance_order(request, order_number, "Started", "Order Started")
            rider = getattr(request.user, "rider_profile", None)
            if rider:

                def _notify_rider_start_alt():
                    try:
                        notify_rider(
                            rider=rider,
                            title="Trip Started 🚀",
                            body=f"You're on your way to pick up order #{order_number}.",
                            data={"order_number": order_number, "status": "Started"},
                        )
                    except Exception as exc:
                        logger.warning(f"Start notification failed: {exc}")

                threading.Thread(target=_notify_rider_start_alt, daemon=True).start()
            return response

        elif action == "pickup":
            return _advance_order(
                request, order_number, "Fulfilling", "Order Picked Up"
            )

        elif action == "arrived":
            return _advance_order(
                request, order_number, "Arrived", "Rider Arrived at Pickup"
            )

        return Response(
            {"error": "Invalid action. Use start, pickup, or arrived."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class OrderCompleteView(APIView):
    """
    Endpoint for riders to mark an entire order as completed.
    POST /api/orders/complete/

    Completion flow:
      1. If COD order → verify rider wallet has enough balance (they must
         have collected the cash and deposited it). Debit that amount.
      2. Calculate rider net earning using commission_rate from SystemSettings
         (default 20 %). Create RiderEarning record and credit rider wallet.
      3. Mark pending RiderCodRecord as remitted.
      4. Advance order status to Done, mark deliveries Delivered.
      5. Send push notification to rider.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    # COD payment methods that require a wallet balance check
    COD_METHODS = {"cash", "cash_on_pickup", "receiver_pays"}
    # Default commission percentage if SystemSettings row doesn't exist yet
    DEFAULT_COMMISSION_PCT = Decimal("20.00")

    @exception_advice(model_object=ErrorLog)
    def post(self, request, order_number):
        if not order_number:
            return service_response(
                status="error",
                message="order_number is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return service_response(
                status="error",
                message="Order not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return service_response(
                status="error",
                message="Rider profile not found.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Proximity check for order completion (check final delivery location)
        # Fetch rider's last known location from the database (since no payload is sent)
        lat = rider.current_latitude
        lng = rider.current_longitude

        if lat is None or lng is None:
            return service_response(
                status="error",
                message="Rider location not found. Please ensure GPS is active.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        lat = float(lat)
        lng = float(lng)

        # Find the final delivery (highest sequence)
        final_delivery = order.deliveries.order_by("-sequence").first()
        if (
            final_delivery
            and final_delivery.dropoff_latitude is not None
            and final_delivery.dropoff_longitude is not None
        ):
            origin = {"lat": lat, "lng": lng}
            drop = {
                "lat": float(final_delivery.dropoff_latitude),
                "lng": float(final_delivery.dropoff_longitude),
            }
            route_data = calculate_route(origin=origin, destinations=[drop])

            if route_data:
                dist = float(route_data["distance_km"])
            else:
                from dispatcher.models import Zone

                dist = Zone.haversine_distance(
                    lat,
                    lng,
                    final_delivery.dropoff_latitude,
                    final_delivery.dropoff_longitude,
                )

            if dist > 2.0:  # 2000 meters
                return service_response(
                    status="error",
                    message=f"You are too far from the final delivery location ({dist:.2f}km). Please move closer.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        # ── Step 1: COD wallet balance check ─────────────────────────────────
        cod_total = Decimal("0.00")

        # ── Step 2: Calculate and record rider earnings ───────────────────────
        settings_obj = SystemSettings.objects.first()
        commission_pct = (
            settings_obj.commission_pct if settings_obj else self.DEFAULT_COMMISSION_PCT
        )

        order_amount = Decimal(str(order.total_amount))
        commission_amount = (commission_pct / Decimal("100")) * order_amount
        net_earning = commission_amount

        # Create or update RiderEarning for this order (idempotent)
        earning, _ = RiderEarning.objects.get_or_create(
            order=order,
            defaults={
                "rider": rider,
                "base_fare": order_amount,
                "commission_pct": commission_pct,
                "commission_amount": commission_amount,
                "net_earning": commission_amount,
                "cod_amount": cod_total,
            },
        )

        # Credit rider wallet with net earning
        rider_wallet_for_credit, _ = Wallet.objects.get_or_create(user=rider.user)
        rider_wallet_for_credit.credit(
            amount=commission_amount,
            description=f"Trip earning for order #{order_number}",
            reference=f"EARN-{order_number}-{order.id.hex[:8].upper()}",
            metadata={
                "order_number": order_number,
                "gross": str(order_amount),
                "commission_pct": str(commission_pct),
                "net_earning": str(commission_amount),
            },
        )

        # ── Step 3: Mark COD record as remitted ──────────────────────────────
        # if order.collect_on_delivery:
        #     RiderCodRecord.objects.filter(
        #         order=order, rider=rider, status=RiderCodRecord.Status.PENDING
        #     ).update(
        #         status=RiderCodRecord.Status.REMITTED,
        #         remitted_at=timezone.now(),
        #     )

        # ── Step 4: Mark all deliveries Delivered, advance order to Done ─────
        deliveries = order.deliveries.exclude(status="Delivered")
        for d in deliveries:
            d.status = "Delivered"
            d.delivered_at = timezone.now()
            d.save(update_fields=["status", "delivered_at"])

        # ── Step 5: Push notification ─────────────────────────────────────────
        def _notify_order_done():
            try:
                notify_rider(
                    rider=rider,
                    title="Order Completed 🎉",
                    body=f"Order #{order_number} completed. ₦{net_earning} credited to your wallet.",
                    data={
                        "order_number": order_number,
                        "net_earning": str(net_earning),
                    },
                )
            except Exception as exc:
                logger.warning(
                    f"Failed to send completion notification to rider {rider.rider_id}: {exc}"
                )

        threading.Thread(target=_notify_order_done, daemon=True).start()

        # Trigger F2 email. The `_advance_order` call below also triggers it if new_status is "Done",
        # but we can rely on `_advance_order` to handle it cleanly.

        return _advance_order(
            request, order_number, "Done", "Order Completed (All Deliveries)"
        )


class AssignedOrderDetailView(APIView):
    """
    Get details of a specific assigned order.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request, order_number):
        # Get rider profile
        rider_profile = getattr(request.user, "rider_profile", None)
        if not rider_profile:
            return Response(
                {"success": False, "message": "Authenticated user is not a driver."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            order = (
                Order.objects.filter(rider=rider_profile, order_number=order_number)
                .select_related("vehicle", "user")
                .prefetch_related("deliveries", "rider_offers")
                .get()
            )
        except Order.DoesNotExist:
            return Response(
                {"success": False, "message": "Assigned order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AssignedOrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssignedRoutesView(APIView):
    """
    Get list of orders assigned to the authenticated rider,
    formatted as routes and stops.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        # excluded_statuses = ["Done", "CustomerCanceled", "RiderCanceled", "Failed"]
        statuses = ["Pending", "Assigned", "PickedUp", "Started"]
        order_status = request.query_params.get("status", "active")
        if order_status == "done":
            statuses = ["Done"]

        # Get rider profile
        rider_profile = getattr(request.user, "rider_profile", None)
        if not rider_profile:
            return Response(
                {"success": False, "message": "Authenticated user is not a driver."},
                status=status.HTTP_403_FORBIDDEN,
            )

        orders = (
            Order.objects.filter(rider=rider_profile)
            .filter(status__in=statuses)
            .select_related("vehicle", "user")
            .prefetch_related("deliveries", "rider_offers")
            .order_by("-created_at")
        )

        serializer = AssignedRouteSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsRider])
def cancel_order(request, order_id):
    """POST /api/orders/<id>/rider-cancel/"""
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    ser = OrderCancelSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    # Get rider profile
    rider = request.user.rider_profile
    order.status = "Pending"
    order.canceled_at = timezone.now()
    order.cancellation_reason = ser.validated_data.get("reason")
    order.rider = None
    order.save()

    rider.current_order = None
    rider.status = Rider.Status.ONLINE
    rider.save(update_fields=["current_order", "status"])

    return Response({"status": "canceled"})


class DeliveryStartView(APIView):
    """
    Endpoint for riders to mark a specific delivery as In Transit.
    POST /api/orders/delivery/<delivery_id>/start/
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
    def post(self, request, delivery_id):
        try:
            delivery = Delivery.objects.get(id=delivery_id)
            order = delivery.order
        except Delivery.DoesNotExist:
            return Response(
                {"error": "Delivery not found"}, status=status.HTTP_404_NOT_FOUND
            )

        ser = OrderStatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        old_status = delivery.status
        delivery.status = "InTransit"
        delivery.save(update_fields=["status"])

        # Update order status if it's currently PickedUp
        if order.status == "PickedUp":
            order.status = "Started"
            order.save(update_fields=["status", "updated_at"])

        # Update rider location if provided
        rider_profile = getattr(request.user, "rider_profile", None)
        if rider_profile and ser.validated_data.get("latitude"):
            rider_profile.current_latitude = ser.validated_data["latitude"]
            rider_profile.current_longitude = ser.validated_data["longitude"]
            rider_profile.last_location_update = timezone.now()
            rider_profile.save(
                update_fields=[
                    "current_latitude",
                    "current_longitude",
                    "last_location_update",
                ]
            )

        order_event_signal.send(
            sender=self.__class__,
            order=order,
            event="Delivery Started",
            description=f"Delivery to {delivery.receiver_name} started by rider {request.user.contact_name or request.user.phone}",
            created_by=request.user,
        )

        return Response({"status": "InTransit", "previous": old_status})



class DeliveryCompleteView(APIView):
    """
    Endpoint for riders to mark a specific delivery as Delivered.
    POST /api/orders/delivery/<delivery_id>/deliver/
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def post(self, request, delivery_id):
        try:
            delivery = Delivery.objects.select_for_update().get(id=delivery_id)
            order = delivery.order
        except Delivery.DoesNotExist:
            return Response(
                {"error": "Delivery not found"}, status=status.HTTP_404_NOT_FOUND
            )

        ser = OrderStatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # Proximity check for specific delivery completion
        lat = ser.validated_data.get("latitude")
        lng = ser.validated_data.get("longitude")

        if lat is not None and lng is not None:
            if (
                delivery.dropoff_latitude is not None
                and delivery.dropoff_longitude is not None
            ):
                from dispatcher.models import Zone

                dist = Zone.haversine_distance(
                    lat, lng, delivery.dropoff_latitude, delivery.dropoff_longitude
                )
                if dist > 0.5:  # 500 meters
                    return Response(
                        {
                            "error": f"You are too far from the delivery location ({dist:.2f}km). Please move closer."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        old_status = delivery.status
        delivery.status = "Delivered"
        delivery.delivered_at = timezone.now()
        delivery.save(update_fields=["status", "delivered_at"])

        # Advance Order to Done once all deliveries are marked Delivered.
        all_delivered = not order.deliveries.exclude(status="Delivered").exists()
        if all_delivered:
            order.status = "Done"
            order.completed_at = order.completed_at or timezone.now()
            order.save(update_fields=["status", "updated_at", "completed_at"])

            # Trigger order-completed webhook in background
            def _trigger_delivery_completed():
                try:
                    from webhooks.utils import trigger_webhook
                    from .serializers import OrderSerializer

                    payload = {
                        "event": "order-completed",
                        "timestamp": (
                            order.completed_at.isoformat()
                            if order.completed_at
                            else timezone.now().isoformat()
                        ),
                        "data": OrderSerializer(order).data,
                    }
                    trigger_webhook("order-completed", payload)
                except Exception as e:
                    logger.error(
                        f"Failed to trigger order-completed webhook in DeliveryCompleteView: {e}"
                    )

            threading.Thread(target=_trigger_delivery_completed, daemon=True).start()

        # Update rider location if provided
        rider_profile = getattr(request.user, "rider_profile", None)
        if rider_profile and ser.validated_data.get("latitude"):
            rider_profile.current_latitude = ser.validated_data["latitude"]
            rider_profile.current_longitude = ser.validated_data["longitude"]
            rider_profile.last_location_update = timezone.now()
            rider_profile.save(
                update_fields=[
                    "current_latitude",
                    "current_longitude",
                    "last_location_update",
                ]
            )

        order_event_signal.send(
            sender=self.__class__,
            order=order,
            event="Delivery Completed",
            description=f"Delivery to {delivery.receiver_name} completed by rider {request.user.contact_name or request.user.phone}",
            created_by=request.user,
        )

        return Response({"status": "Delivered", "previous": old_status})



class MergeGroupedOrdersView(APIView):
    """API view to merge multiple grouped orders into a parent order."""

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        serializer = MergeGroupedOrdersSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order_ids = serializer.validated_data["order_ids"]
        orders = Order.objects.filter(id__in=order_ids)

        # Take common info from the first order to create parent
        first_order = orders.first()

        # Calculate aggregated total_amount
        total_amount = sum(o.total_amount for o in orders)

        # Create Parent Order
        parent_order = Order.objects.create(
            user=request.user,
            mode="grouped",
            vehicle=first_order.vehicle,
            pickup_address=first_order.pickup_address,
            sender_name=first_order.sender_name,
            sender_phone=first_order.sender_phone,
            total_amount=total_amount,
            status="Pending",
            payment_method=first_order.payment_method,
            distance_km=sum(o.distance_km for o in orders if o.distance_km) or 0,
            duration_minutes=sum(
                o.duration_minutes for o in orders if o.duration_minutes
            )
            or 0,
        )

        # Link sub-orders to the new parent
        orders.update(parent_order=parent_order)

        return service_response(
            status="success",
            message=f"Successfully merged {len(order_ids)} orders into parent {parent_order.order_number}",
            data={
                "parent_order_number": parent_order.order_number,
                "parent_id": str(parent_order.id),
            },
            status_code=201,
        )


# ---------------------------------------------------------------------------
# SmartParcel Locker Delivery Integration
# ---------------------------------------------------------------------------


def _sp() -> SmartPercelIntegration:
    """Return a shared SmartPercelIntegration instance."""
    return SmartPercelIntegration()


class SmartParcelStatesView(APIView):
    """List all states where SmartParcel operates."""

    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    @exception_advice(model_object=ErrorLog)
    def get(self, request, *args, **kwargs):
        ok, data = _sp().list_states()
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel states retrieved successfully.",
            data=data,
            status_code=200,
        )


class SmartParcelCitiesByStateView(APIView):
    """List cities for a specific SmartParcel state."""

    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(cache_page(60 * 30))
    @exception_advice(model_object=ErrorLog)
    def get(self, request, state_id: str, *args, **kwargs):
        ok, data = _sp().list_cities_by_state(state_id)
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel cities for state retrieved successfully.",
            data=data,
            status_code=200,
        )


class SmartParcelBoxesByCityView(APIView):
    """List all SmartParcel boxes in a specific city."""

    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(cache_page(60 * 30))
    @exception_advice(model_object=ErrorLog)
    def get(self, request, city_id: str, *args, **kwargs):
        ok, data = _sp().list_boxes_by_city(city_id)
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel boxes for city retrieved successfully.",
            data=data,
            status_code=200,
        )


class SmartParcelAssignedBoxesByCityView(APIView):
    """List SmartParcel boxes assigned to the merchant, filtered by city."""

    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(cache_page(60 * 30))
    @exception_advice(model_object=ErrorLog)
    def get(self, request, city_id: str, *args, **kwargs):
        ok, data = _sp().list_assigned_boxes()
        if not ok:
            raise ServiceException(status_code=502, message=data)

        # SmartParcel API returns boxes in 'boxes' field for this endpoint
        boxes = data.get("boxes", [])
        if not isinstance(boxes, list):
            # Fallback if the structure is different
            boxes = data if isinstance(data, list) else []

        # Filter by city_id
        filtered_boxes = [b for b in boxes if str(b.get("cityid")) == str(city_id)]

        return service_response(
            status="success",
            message=f"SmartParcel assigned boxes for city {city_id} retrieved successfully.",
            data=filtered_boxes,
            status_code=200,
        )


class SmartParcelBoxDetailView(APIView):
    """Retrieve details of a single SmartParcel box."""

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request, box_id: str, *args, **kwargs):
        ok, data = _sp().get_box_details(box_id)
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel box details retrieved successfully.",
            data=data,
            status_code=200,
        )


class SmartParcelAvailableBoxesView(APIView):
    """List all SmartParcel boxes in a specific city (wrapper for business logic)."""

    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(cache_page(60 * 30))
    @exception_advice(model_object=ErrorLog)
    def get(self, request, *args, **kwargs):
        city_id = request.query_params.get("city_id")
        if not city_id:
            raise ServiceException(status_code=400, message="city_id is required.")

        ok, data = _sp().list_boxes_by_city(city_id)
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel boxes for city retrieved successfully.",
            data=data,
            status_code=200,
        )


class SmartParcelLockerSizesView(APIView):
    """List all locker sizes on the SmartParcel network."""

    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(cache_page(60 * 30))
    @exception_advice(model_object=ErrorLog)
    def get(self, request, *args, **kwargs):
        ok, data = _sp().list_locker_sizes()
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel locker sizes retrieved successfully.",
            data=data,
            status_code=200,
        )


class SmartParcelPendingPickupsView(APIView):
    """List all pending parcels ready for pickup on the SmartParcel network."""

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request, *args, **kwargs):
        ok, data = _sp().list_pending_pickups()
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel pending pickups retrieved successfully.",
            data=data,
            status_code=200,
        )


class SmartParcelResolveCollectCodeView(APIView):
    """Resolve a SmartParcel collect code to a pending parcel detail."""

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request, collect_code: str, *args, **kwargs):
        ok, data = _sp().list_pending_pickups()
        if not ok:
            raise ServiceException(status_code=502, message=data)

        parcels = data.get("parcels") or []
        if not isinstance(parcels, list):
            parcels = []

        # Find the parcel with the matching collectcode (case-insensitive)
        found_parcel = next(
            (
                p
                for p in parcels
                if str(p.get("parcelreferencenumber")).strip().lower()
                == collect_code.strip().lower()
            ),
            None,
        )

        if not found_parcel:
            return service_response(
                status="error",
                message=f"No pending parcel found for collect code '{collect_code}'.",
                data={},
                status_code=404,
            )

        return service_response(
            status="success",
            message="SmartParcel parcel resolved successfully.",
            data=found_parcel,
            status_code=200,
        )


class SmartParcelCreateParcelView(APIView):
    """Create a new SmartParcel parcel."""

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request, *args, **kwargs):
        serializer = CreateParcelSerializer(data=request.data)
        if not serializer.is_valid():
            raise ServiceException(
                status_code=400,
                message=str(serializer.errors),
            )

        # Map to V2 Business API keys
        vd = serializer.validated_data
        payload = {
            "recipientname": vd["receiver_name"],
            "recipientemail": vd.get("receiver_email", ""),
            "recipientphone": vd["receiver_phone"],
            "sendername": vd["sender_name"],
            "senderemail": vd.get("sender_email", ""),
            "senderphone": vd["sender_phone"],
            "boxid": vd["box_id"],
            "sizeid": vd["locker_size_id"],
            "parceldescription": vd.get("description", ""),
        }

        ok, data = _sp().create_parcel(payload)
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel parcel created successfully.",
            data=data,
            status_code=201,
        )


class SmartParcelParcelDetailView(APIView):
    """Retrieve details of a SmartParcel parcel."""

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request, tracking_number: str, *args, **kwargs):
        ok, data = _sp().get_parcel_details(tracking_number)
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel parcel details retrieved successfully.",
            data=data,
            status_code=200,
        )


class SmartParcelCancelParcelView(APIView):
    """Cancel an existing SmartParcel parcel."""

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request, tracking_number: str, *args, **kwargs):
        ok, data = _sp().cancel_parcel(tracking_number)
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel parcel cancelled successfully.",
            data=data,
            status_code=200,
        )


class SmartParcelSimulateDropView(APIView):
    """[Sandbox] Simulate dropping a parcel into a locker box.

    Triggers the 'dropped' state transition on a parcel so the collect-code
    flow can be tested end-to-end without physical hardware.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request, *args, **kwargs):
        box_id = request.data.get("box_id")
        unlock_code = request.data.get("unlock_code")
        if not box_id or not unlock_code:
            raise ServiceException(
                status_code=400, message="box_id and unlock_code are required."
            )

        ok, data = _sp().simulate_drop_parcel(box_id, unlock_code)
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel parcel drop simulated successfully.",
            data=data,
            status_code=200,
        )


class SmartParcelSimulateCollectView(APIView):
    """[Sandbox] Simulate a recipient collecting a parcel from a locker.

    Triggers the 'collected' state transition on a parcel so the full
    pickup workflow can be tested end-to-end without physical hardware.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request, *args, **kwargs):
        box_id = request.data.get("box_id")
        unlock_code = request.data.get("unlock_code")
        if not box_id or not unlock_code:
            raise ServiceException(
                status_code=400, message="box_id and unlock_code are required."
            )

        ok, data = _sp().simulate_collect_parcel(box_id, unlock_code)
        if not ok:
            raise ServiceException(status_code=502, message=data)
        return service_response(
            status="success",
            message="SmartParcel parcel collect simulated successfully.",
            data=data,
            status_code=200,
        )
