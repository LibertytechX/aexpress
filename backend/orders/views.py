from dispatcher.models import SystemSettings
import logging
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Order, Delivery, Vehicle, OrderEvent
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
)
from .permissions import IsRider
from dispatcher.models import Rider
from dispatcher.utils import emit_activity
from wallet.models import Wallet
from wallet.escrow import EscrowManager
from riders.notifications import notify_rider
from riders.models import RiderEarning, RiderCodRecord

logger = logging.getLogger(__name__)


class VehicleListView(APIView):
    """API endpoint to list all available vehicles."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all active vehicles with pricing."""
        vehicles = Vehicle.objects.filter(is_active=True)
        serializer = VehicleSerializer(vehicles, many=True)

        return Response(
            {"success": True, "vehicles": serializer.data}, status=status.HTTP_200_OK
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

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """Create a Quick Send order with single delivery."""
        serializer = QuickSendSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # Get vehicle
        vehicle = Vehicle.objects.get(name=data["vehicle"], is_active=True)

        # Calculate total amount using new fare structure
        distance_km = data.get("distance_km", 0)
        duration_minutes = data.get("duration_minutes", 0)
        total_amount = vehicle.calculate_fare(distance_km, duration_minutes)

        # Create order
        order = Order.objects.create(
            user=request.user,
            mode="quick",
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
            sequence=1,
        )

        # Emit activity event for live feed
        merchant_name = (
            getattr(request.user, "business_name", None)
            or getattr(request.user, "contact_name", None)
            or "Unknown"
        )
        emit_activity(
            event_type="new_order",
            order_id=order.order_number,
            text=f"New order {order.order_number} from {merchant_name}",
            color="gold",
            metadata={
                "merchant": merchant_name,
                "amount": str(total_amount),
                "pickup": data["pickup_address"],
                "dropoff": data["dropoff_address"],
            },
        )

        # Hold funds in escrow if payment method is wallet
        if data["payment_method"] == "wallet":
            try:
                wallet = Wallet.objects.get(user=request.user)

                # Hold funds in escrow
                try:
                    EscrowManager.hold_funds(
                        wallet=wallet,
                        amount=total_amount,
                        order_number=order.order_number,
                        description=f"Escrow hold for Quick Send order #{order.order_number}",
                    )

                    # Mark order as having escrow held
                    order.escrow_held = True
                    order.save()

                except ValueError as e:
                    # Insufficient balance - rollback order
                    order.delete()
                    return Response(
                        {"success": False, "errors": {"wallet": [str(e)]}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            except Wallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = Wallet.objects.create(user=request.user)
                order.delete()
                return Response(
                    {
                        "success": False,
                        "errors": {
                            "wallet": [
                                "Insufficient wallet balance. Please fund your wallet first."
                            ]
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Notify all online riders about the new order
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

        # Return created order
        order_serializer = OrderSerializer(order)

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

    @transaction.atomic
    def post(self, request):
        """Create a Multi-Drop order with multiple deliveries."""
        serializer = MultiDropSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # Get vehicle
        vehicle = Vehicle.objects.get(name=data["vehicle"], is_active=True)

        # Calculate total amount using new fare structure
        num_deliveries = len(data["deliveries"])
        distance_km = data.get("distance_km", 0)
        duration_minutes = data.get("duration_minutes", 0)
        unit_fare = vehicle.calculate_fare(distance_km, duration_minutes)
        total_amount = unit_fare * num_deliveries

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
                sequence=idx,
            )

        # Hold funds in escrow if payment method is wallet
        if data["payment_method"] == "wallet":
            try:
                wallet = Wallet.objects.get(user=request.user)

                # Hold funds in escrow
                try:
                    EscrowManager.hold_funds(
                        wallet=wallet,
                        amount=total_amount,
                        order_number=order.order_number,
                        description=f"Escrow hold for Multi-Drop order #{order.order_number} ({num_deliveries} deliveries)",
                    )

                    # Mark order as having escrow held
                    order.escrow_held = True
                    order.save()

                except ValueError as e:
                    # Insufficient balance - rollback order
                    order.delete()
                    return Response(
                        {"success": False, "errors": {"wallet": [str(e)]}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            except Wallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = Wallet.objects.create(user=request.user)
                order.delete()
                return Response(
                    {
                        "success": False,
                        "errors": {
                            "wallet": [
                                "Insufficient wallet balance. Please fund your wallet first."
                            ]
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Notify all online riders about the new order
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

        # Return created order
        order_serializer = OrderSerializer(order)

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

    @transaction.atomic
    def post(self, request):
        """Create a Bulk Import order with multiple deliveries."""
        serializer = BulkImportSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # Get vehicle
        vehicle = Vehicle.objects.get(name=data["vehicle"], is_active=True)

        # Calculate total amount using new fare structure
        num_deliveries = len(data["deliveries"])
        distance_km = data.get("distance_km", 0)
        duration_minutes = data.get("duration_minutes", 0)
        unit_fare = vehicle.calculate_fare(distance_km, duration_minutes)
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
                sequence=idx,
            )

        # Hold funds in escrow if payment method is wallet
        if data["payment_method"] == "wallet":
            try:
                wallet = Wallet.objects.get(user=request.user)

                # Hold funds in escrow
                try:
                    EscrowManager.hold_funds(
                        wallet=wallet,
                        amount=total_amount,
                        order_number=order.order_number,
                        description=f"Escrow hold for Bulk Import order #{order.order_number} ({num_deliveries} deliveries)",
                    )

                    # Mark order as having escrow held
                    order.escrow_held = True
                    order.save()

                except ValueError as e:
                    # Insufficient balance - rollback order
                    order.delete()
                    return Response(
                        {"success": False, "errors": {"wallet": [str(e)]}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            except Wallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = Wallet.objects.create(user=request.user)
                order.delete()
                return Response(
                    {
                        "success": False,
                        "errors": {
                            "wallet": [
                                "Insufficient wallet balance. Please fund your wallet first."
                            ]
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Notify all online riders about the new order
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

        # Return created order
        order_serializer = OrderSerializer(order)

        return Response(
            {
                "success": True,
                "message": f"Bulk Import order created with {num_deliveries} deliveries!",
                "order": order_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class OrderListView(APIView):
    """API endpoint to list all orders for the authenticated user."""

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
            .select_related("vehicle")
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


class OrderDetailView(APIView):
    """API endpoint to get details of a specific order."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_number):
        """Get order details by order number."""
        try:
            order = (
                Order.objects.select_related("vehicle")
                .prefetch_related("deliveries")
                .get(order_number=order_number)
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

    permission_classes = [permissions.IsAuthenticated]

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
            total_amount = vehicle.calculate_fare(
                float(distance_km), int(duration_minutes)
            )

            return Response(
                {
                    "success": True,
                    "price": total_amount,
                    "breakdown": {
                        "base_fare": vehicle.base_fare,
                        "distance_cost": float(distance_km)
                        * float(vehicle.rate_per_km),
                        "time_cost": int(duration_minutes)
                        * float(vehicle.rate_per_minute),
                    },
                },
                status=status.HTTP_200_OK,
            )

        except (ValueError, TypeError) as e:
            return Response(
                {"success": False, "error": f"Invalid data format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
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

    @transaction.atomic
    def post(self, request, order_number):
        """Cancel an order and process refund if needed"""

        # Get cancellation reason
        reason = request.data.get("reason", "Order canceled by merchant")

        # Get the order
        try:
            order = Order.objects.select_for_update().get(
                order_number=order_number, user=request.user
            )
        except Order.DoesNotExist:
            return Response(
                {"error": f"Order {order_number} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if order can be canceled
        if order.status in ["Canceled", "CustomerCanceled"]:
            return Response(
                {"error": "Order is already canceled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status == "Delivered":
            return Response(
                {"error": "Cannot cancel a delivered order"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Once the package has been picked up, cancellation is not allowed
        if order.status in ["PickedUp", "Started"]:
            return Response(
                {"error": "Cannot cancel an order that has already been picked up"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if escrow was released (delivery completed)
        if order.escrow_held and order.escrow_released:
            return Response(
                {
                    "error": "Cannot cancel order - delivery already completed and funds released"
                },
                status=status.HTTP_400_BAD_REQUEST,
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
                return Response(
                    {"error": f"Failed to process refund: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Update order status
        old_status = order.status
        order.status = "CustomerCanceled"
        order.updated_at = timezone.now()
        order.save()

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

        # Prepare response
        response_data = {
            "success": True,
            "message": f"Order {order_number} has been canceled",
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

        return Response(response_data, status=status.HTTP_200_OK)


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

    old_status = order.status
    order.status = new_status
    if new_status == "PickedUp" and not order.picked_up_at:
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

    OrderEvent.objects.create(
        order=order,
        event=event_desc,
        description=f"By rider {request.user.contact_name or request.user.phone}",
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

    def post(self, request):
        order_number = request.data.get("order_number")
        if not order_number:
            return Response(
                {"error": "order_number is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return _advance_order(request, order_number, "PickedUp", "Order Picked Up")


class OrderStartView(APIView):
    """
    Endpoint for riders to mark an order as started (trip to pickup).
    POST /api/orders/start/
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def post(self, request):
        order_number = request.data.get("order_number")
        if not order_number:
            return Response(
                {"error": "order_number is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # TODO: check if the rider is assigned to this order

        response = _advance_order(request, order_number, "Started", "Order Started")

        # Push notification — fire-and-forget, don't block the response
        try:
            rider = getattr(request.user, "rider_profile", None)
            if rider:
                notify_rider(
                    rider=rider,
                    title="Trip Started 🚀",
                    body=f"You're on your way to pick up order #{order_number}.",
                    data={"order_number": order_number, "status": "Started"},
                )
        except Exception as exc:
            logger.warning(f"Start notification failed: {exc}")

        return response


class OrderArrivedView(APIView):
    """
    Endpoint for riders to mark themselves as arrived at pickup.
    POST /api/orders/arrived/
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

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

    @transaction.atomic
    def post(self, request, order_number):
        if not order_number:
            return Response(
                {"error": "order_number is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = Order.objects.select_for_update().get(order_number=order_number)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return Response(
                {"error": "Rider profile not found."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ── Step 1: COD wallet balance check ─────────────────────────────────
        is_cod = order.payment_method in self.COD_METHODS
        cod_total = Decimal("0.00")

        if is_cod:
            # Sum COD across all deliveries for this order
            from django.db.models import Sum

            cod_total = order.deliveries.aggregate(Sum("cod_amount"))[
                "cod_amount__sum"
            ] or Decimal("0.00")

            if cod_total > 0:
                try:
                    rider_wallet = Wallet.objects.get(user=rider.user)
                except Wallet.DoesNotExist:
                    return Response(
                        {
                            "error": "Rider wallet not found. Cannot process COD payment."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not rider_wallet.can_debit(cod_total):
                    return Response(
                        {
                            "error": (
                                f"Insufficient wallet balance for COD settlement. "
                                f"Required: ₦{cod_total}, Available: ₦{rider_wallet.balance}"
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Debit COD amount from rider wallet
                rider_wallet.debit(
                    amount=cod_total,
                    description=f"COD remittance for order #{order_number}",
                    reference=f"COD-{order_number}-{order.id.hex[:8].upper()}",
                    metadata={"order_number": order_number, "order_id": str(order.id)},
                )

        # ── Step 2: Calculate and record rider earnings ───────────────────────
        settings_obj = SystemSettings.objects.first()
        # SystemSettings stores cod_pct_fee; we repurpose a rider-specific
        # commission field if it exists — fall back to hard-coded default.
        commission_pct = settings_obj.commission_pct

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
        if is_cod and cod_total > 0:
            RiderCodRecord.objects.filter(
                order=order, rider=rider, status=RiderCodRecord.Status.PENDING
            ).update(
                status=RiderCodRecord.Status.REMITTED,
                remitted_at=timezone.now(),
            )

        # ── Step 4: Mark all deliveries Delivered, advance order to Done ─────
        deliveries = order.deliveries.exclude(status="Delivered")
        for d in deliveries:
            d.status = "Delivered"
            d.delivered_at = timezone.now()
            d.save(update_fields=["status", "delivered_at"])

        # ── Step 5: Push notification ─────────────────────────────────────────
        try:
            notify_rider(
                rider=rider,
                title="Order Completed 🎉",
                body=f"Order #{order_number} completed. ₦{net_earning} credited to your wallet.",
                data={"order_number": order_number, "net_earning": str(net_earning)},
            )
        except Exception as exc:
            logger.warning(
                f"Failed to send completion notification to rider {rider.rider_id}: {exc}"
            )

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

    OrderEvent.objects.create(
        order=order,
        event="Driver Canceled",
        description=f"Canceled by {request.user.contact_name or request.user.phone}: {ser.validated_data['reason']}",
    )

    return Response({"status": "canceled"})


class DeliveryStartView(APIView):
    """
    Endpoint for riders to mark a specific delivery as In Transit.
    POST /api/orders/delivery/<delivery_id>/start/
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

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

        OrderEvent.objects.create(
            order=order,
            event="Delivery Started",
            description=f"Delivery to {delivery.receiver_name} started by rider {request.user.contact_name or request.user.phone}",
        )

        return Response({"status": "InTransit", "previous": old_status})


class DeliveryCompleteView(APIView):
    """
    Endpoint for riders to mark a specific delivery as Delivered.
    POST /api/orders/delivery/<delivery_id>/deliver/
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @transaction.atomic
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

            OrderEvent.objects.create(
                order=order,
                event="Order Completed",
                description="All deliveries completed.",
            )

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

        OrderEvent.objects.create(
            order=order,
            event="Delivery Completed",
            description=f"Delivery to {delivery.receiver_name} completed by rider {request.user.contact_name or request.user.phone}",
        )

        return Response({"status": "Delivered", "previous": old_status})
