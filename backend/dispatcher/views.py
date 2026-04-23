import logging
import datetime
from sparky_utils.response import service_response
from sparky_utils.advice import exception_advice

from rest_framework import viewsets, permissions, status, views, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings

from .authentication import ServiceAPIKeyAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination
from .models import (
    Rider,
    ActivityFeed,
    Zone,
    RelayNode,
    VehicleAsset,
    VerticalLead,
    Vertical,
    RiderDutyLog,
    Merchant,
    MerchantAPIKey,
)
from .serializers import (
    RiderSerializer,
    ZoneSerializer,
    RelayNodeSerializer,
    VehicleAssetSerializer,
    VerticalSerializer,
)
from .utils import emit_activity
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Count, Q, Prefetch
from django.utils import timezone

# Merchant API Key imports
from authentication.services import OTPService
from devs.models import ErrorLog
from sparky_utils.exceptions import ServiceException
import secrets
import hashlib

from riders.notifications import notify_rider
from riders.views import publish_order_assigned_event
from .permissions import IsDispatcher, IsZoneLead, IsDispatcherAdmin
from .tasks import send_merchant_notification
from orders.serializers import MergeGroupedOrdersSerializer
from django.db import transaction

logger = logging.getLogger(__name__)

User = get_user_model()


class RiderViewSet(viewsets.ModelViewSet):
    queryset = Rider.objects.all().select_related(
        "user", "vehicle_type", "vehicle_asset", "hub", "hub__zone"
    )
    serializer_class = RiderSerializer
    authentication_classes = [
        ServiceAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # user = self.request.user
        # role = user.dispatcher_profile.role
        # if the dispatcher role is zone_lead
        # if role == "zone_lead":
        #     try:
        #         zone_lead = VerticalLead.objects.get(user=user)
        #         zones = zone_lead.area_zones.all()
        #         relay_nodes = RelayNode.objects.filter(zone__in=zones)
        #         return Rider.objects.filter(hub__in=relay_nodes).select_related(
        #             "user", "vehicle_type", "vehicle_asset", "hub", "hub__zone"
        #         )
        #     except VerticalLead.DoesNotExist:
        #         pass
        return Rider.objects.all().select_related(
            "user", "vehicle_type", "vehicle_asset", "hub", "hub__zone"
        )

    @action(detail=True, methods=["post"], url_path="reset_password")
    def reset_password(self, request, pk=None):
        """Allow dispatcher to set a new password for a rider account."""
        rider = self.get_object()
        new_password = request.data.get("new_password", "")
        if not new_password or len(new_password) < 6:
            return Response(
                {"error": "Password must be at least 6 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        rider.user.set_password(new_password)
        rider.user.save(update_fields=["password"])
        return Response({"success": True, "message": "Password updated successfully."})

    @action(detail=True, methods=["post"], url_path="assign_vehicle")
    def assign_vehicle(self, request, pk=None):
        """Assign or unassign a vehicle asset to a rider."""
        rider = self.get_object()
        vehicle_asset_id = request.data.get("vehicle_asset_id")

        if vehicle_asset_id:
            from .models import VehicleAsset

            try:
                vehicle = VehicleAsset.objects.get(id=vehicle_asset_id)
            except VehicleAsset.DoesNotExist:
                return Response(
                    {"error": "Vehicle asset not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            rider.vehicle_asset = vehicle
        else:
            rider.vehicle_asset = None

        rider.save(update_fields=["vehicle_asset"])
        serializer = self.get_serializer(rider)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="toggle_duty")
    def toggle_duty(self, request, pk=None):
        """Toggle a rider's duty status (online/offline)."""
        rider = self.get_object()
        status_val = request.data.get("status")

        if status_val == Rider.Status.ONLINE:
            if rider.status != Rider.Status.ONLINE:
                rider.go_online()
                # Open a new duty log entry
                RiderDutyLog.objects.create(rider=rider, went_online=timezone.now())
            return Response({"status": "success", "message": "Rider is now online"})
        elif status_val == Rider.Status.OFFLINE:
            if rider.status != Rider.Status.OFFLINE:
                rider.go_offline()
                # Close the most recent open duty log
                open_log = (
                    RiderDutyLog.objects.filter(rider=rider, went_offline__isnull=True)
                    .order_by("-went_online")
                    .first()
                )
                if open_log:
                    now = timezone.now()
                    open_log.went_offline = now
                    open_log.duration_minutes = int(
                        (now - open_log.went_online).total_seconds() / 60
                    )
                    open_log.save(update_fields=["went_offline", "duration_minutes"])
            return Response({"status": "success", "message": "Rider is now offline"})
        else:
            return Response(
                {"error": "Invalid status. Must be 'online' or 'offline'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["patch"], url_path="update_location")
    def update_location(self, request, pk=None):
        """Update a rider's current GPS coordinates."""
        rider = self.get_object()
        lat = request.data.get("lat")
        lng = request.data.get("lng")

        if lat is None or lng is None:
            return Response(
                {"error": "Both 'lat' and 'lng' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rider.current_latitude = float(lat)
            rider.current_longitude = float(lng)
            rider.last_location_update = timezone.now()
            rider.save(
                update_fields=[
                    "current_latitude",
                    "current_longitude",
                    "last_location_update",
                ]
            )
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid lat/lng values."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(rider.id),
                "rider_id": rider.rider_id,
                "current_latitude": float(rider.current_latitude),
                "current_longitude": float(rider.current_longitude),
                "last_location_update": rider.last_location_update.isoformat(),
            }
        )


class OrderPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500


class OrderViewSet(viewsets.ModelViewSet):
    from orders.models import Order

    queryset = (
        Order.objects.all()
        .select_related("user", "rider", "rider__user")
        .prefetch_related("deliveries")
    )
    from .serializers import (
        OrderSerializer,
        OrderCreateSerializer,
        OrderPriceUpdateSerializer,
    )

    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = [IsDispatcher]

    def paginate_queryset(self, queryset):
        if self.request.query_params.get("all") == "true":
            return None
        return super().paginate_queryset(queryset)

    def get_serializer_class(self):
        if self.action == "create":
            return self.OrderCreateSerializer
        return self.OrderSerializer

    # permission_classes = [permissions.IsAuthenticated]
    lookup_field = "order_number"

    def get_queryset(self):
        qs = super().get_queryset().order_by("-created_at")

        user = self.request.user
        role = getattr(user.dispatcher_profile, "role", None)
        is_all = self.request.query_params.get("all") == "true"

        # if the dispatcher role is zone_lead
        if role == "zone_lead" and not is_all:
            try:
                zone_lead = VerticalLead.objects.get(user=user)
                zones = zone_lead.area_zones.all()
                relay_nodes = RelayNode.objects.filter(zone__in=zones)

                # Filter orders:
                # 1. Status is Pending
                # 2. Assigned rider's hub is in my zones
                # 3. Any relay leg starts/ends in my zones
                qs = qs.filter(
                    Q(status="Pending")
                    | Q(rider__hub__in=relay_nodes)
                    | Q(legs__start_relay_node__in=relay_nodes)
                    | Q(legs__end_relay_node__in=relay_nodes)
                ).distinct()
            except VerticalLead.DoesNotExist:
                pass

        paid_complete = self.request.query_params.get("paid_complete")
        unpaid_complete = self.request.query_params.get("unpaid_complete")

        if paid_complete:
            qs = qs.filter(payment_status="Paid", status="Done")
        if unpaid_complete:
            qs = qs.filter(payment_status="Pending", status="Done")

        # Always prefetch relay legs so the list endpoint returns them too.
        # This keeps relayLegs alive through 60-second auto-refreshes.
        return qs.prefetch_related(
            "legs",
            "legs__start_relay_node",
            "legs__end_relay_node",
            "legs__rider",
            "legs__rider__user",
            "legs__suggested_rider",
            "legs__suggested_rider__user",
            "events",
            "events__created_by",
            "sub_orders",
            "sub_orders__rider",
            "sub_orders__rider__user",
        )

    def create(self, request, *args, **kwargs):
        """Override create to return full OrderSerializer data after creation."""
        from rest_framework.response import Response as DRFResponse
        from rest_framework import status as drf_status
        from django.utils import timezone
        from datetime import timedelta
        from orders.models import Order

        one_minute_ago = timezone.now() - timedelta(minutes=1)
        if Order.objects.filter(
            user=request.user, created_at__gte=one_minute_ago
        ).exists():
            return DRFResponse(
                {
                    "success": False,
                    "errors": {
                        "non_field_errors": [
                            "Please wait a minute before creating another order."
                        ]
                    },
                },
                status=drf_status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = self.OrderCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        response_serializer = self.OrderSerializer(order, context={"request": request})

        # Emit activity event
        merchant_name = (
            getattr(order.user, "business_name", None)
            or getattr(order.user, "contact_name", None)
            or "Unknown"
        )
        pickup = order.pickup_address or ""
        first_delivery = order.deliveries.first()
        dropoff = (first_delivery.dropoff_address if first_delivery else "") or ""
        emit_activity(
            event_type="new_order",
            order_id=order.order_number,
            text=f"New order {order.order_number} from {merchant_name}",
            color="gold",
            metadata={
                "merchant": merchant_name,
                "amount": str(order.total_amount or 0),
                "pickup": pickup,
                "dropoff": dropoff,
            },
        )

        # If a rider is already assigned at creation time, notify them
        if order.rider:
            try:
                notify_rider(
                    rider=order.rider,
                    title="New Order Assigned 📦",
                    body=f"A new order #{order.order_number} from {merchant_name} has been assigned to you.",
                    data={"order_number": order.order_number, "status": "Assigned"},
                )
            except Exception as exc:
                logger.warning(f"New order notification failed: {exc}")

        # Notify the merchant that a rider was assigned to their order
        try:
            merchant_profile = getattr(order.merchant, "merchant_profile", None)
            if merchant_profile:
                send_merchant_notification.delay(
                    merchant_id=str(merchant_profile.id),
                    title="Rider Assigned 🚀",
                    body=f"A rider has been assigned to your order #{order.order_number}.",
                    data={"order_number": order.order_number, "status": "Assigned"},
                    category="order_assigned",
                )
        except Exception as exc:
            logger.warning(f"Merchant assignment notification failed: {exc}")

        return DRFResponse(response_serializer.data, status=drf_status.HTTP_201_CREATED)

    from rest_framework.decorators import action

    @action(detail=True, methods=["post"])
    def assign_rider(self, request, order_number=None):
        order = self.get_object()
        rider_id = request.data.get("rider_id")

        if not rider_id:
            # Unassign request
            order.rider = None
            order.status = "Pending"
            order.save()
            emit_activity(
                event_type="unassigned",
                order_id=order.order_number,
                text=f"{order.order_number} unassigned",
                color="yellow",
                metadata={},
            )
            return Response(self.get_serializer(order).data)

        try:
            rider = Rider.objects.get(rider_id=rider_id)
            order.rider = rider
            order.status = "Assigned"
            order.dispatcher_assigned = True
            # if not getattr(order, "assigned_at", None):
            order.assigned_at = timezone.now()
            order.save()
            rider_name = getattr(rider.user, "contact_name", None) or getattr(
                rider.user, "phone", "Unknown"
            )
            emit_activity(
                event_type="assigned",
                order_id=order.order_number,
                text=f"{order.order_number} assigned to {rider_name}",
                color="blue",
                metadata={"rider": rider_name, "rider_id": rider.rider_id},
            )
            # Push notification to the assigned rider
            try:
                notify_rider(
                    rider=rider,
                    title="New Order Assigned 📦",
                    body=f"Order #{order.order_number} has been assigned to you. Please head to the pickup location.",
                    data={"order_number": order.order_number, "status": "Assigned"},
                )
                publish_order_assigned_event(order, rider)
            except Exception as exc:
                logger.warning(f"Dispatcher assignment notification failed: {exc}")

            # Notify the merchant that a rider was assigned
            try:
                merchant_profile = getattr(order.merchant, "merchant_profile", None)
                if merchant_profile:
                    send_merchant_notification.delay(
                        merchant_id=str(merchant_profile.id),
                        title="Rider Assigned 🚀",
                        body=f"A rider has been assigned to your order #{order.order_number}.",
                        data={"order_number": order.order_number, "status": "Assigned"},
                        category="order_assigned",
                    )
            except Exception as exc:
                logger.warning(f"Merchant assignment notification failed: {exc}")

            return Response(self.get_serializer(order).data)
        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["post"])
    def update_status(self, request, order_number=None):
        """Update Order.status and emit an activity event.

        Accepts both internal names (Started, Done, CustomerCanceled) and
        the display names the frontend uses (In Transit, Delivered, Cancelled,
        Picked Up).
        """
        order = self.get_object()
        new_status = request.data.get("status")
        user = request.user

        # Map frontend display names → internal model values
        DISPLAY_TO_INTERNAL = {
            "Assignment Accepted": "AssignmentAccepted",
            "In Transit": "Started",
            "At Dropoff": "Arrived",  # rider is at the dropoff location
            "Delivered": "Done",
            "Cancelled": "CustomerCanceled",
            "Picked Up": "PickedUp",  # distinct stage; rider app uses this too
        }
        new_status = DISPLAY_TO_INTERNAL.get(new_status, new_status)

        STATUS_MAP = {
            "Pending": ("new_order", "gold"),
            "Assigned": ("assigned", "blue"),
            "PickedUp": ("picked_up", "blue"),
            "Started": ("in_transit", "gold"),
            "Arrived": ("at_dropoff", "orange"),
            "Done": ("delivered", "green"),
            "CustomerCanceled": ("cancelled", "red"),
            "RiderCanceled": ("cancelled", "red"),
            "Failed": ("failed", "red"),
            "AssignmentAccepted": ("assignment_accepted", "green"),
            "AssignmentRejected": ("assignment_rejected", "red"),
        }

        if new_status not in STATUS_MAP:
            return Response(
                {"error": f"Invalid status. Choose from: {list(STATUS_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = order.status
        now = timezone.now()
        order.status = new_status

        # Keep timestamps consistent with rider-app completion flows.
        update_fields = ["status", "updated_at", "payment_status"]
        if new_status == "CustomerCanceled":
            order.payment_status = "Cancelled"
            # cancel the order charge as well
            charge = order.charges.all().first()
            if charge:
                if charge.status == "completed":
                    # refund the user wallet
                    wallet = user.wallet
                    wallet.credit(
                        charge.amount,
                        f"Refund for order #{order.order_number}",
                        f"REFUND-{order.order_number}",
                    )
                charge.status = "canceled"
                charge.save()

        if new_status == "Assigned":
            return Response(
                {"error": f"Please go assign a rider first biko! 😡"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_status == "PickedUp" and not getattr(order, "picked_up_at", None):
            order.picked_up_at = now
            update_fields.append("picked_up_at")
        if new_status == "Arrived" and not getattr(order, "arrived_at", None):
            order.arrived_at = now
            update_fields.append("arrived_at")
        if new_status == "Done" and not getattr(order, "completed_at", None):
            if not order.rider:
                return Response(
                    {
                        "error": f"You can't complete an order that has rider assigned! 😡"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            order.completed_at = now
            update_fields.append("completed_at")

        order.save(update_fields=update_fields)

        # Keep Delivery records in sync so the serializer fallback stays consistent.
        ORDER_TO_DELIVERY_STATUS = {
            "PickedUp": "InTransit",  # rider has picked up → delivery in transit
            "Started": "InTransit",
            "Arrived": "InTransit",  # rider at dropoff; delivery still in progress
            "Done": "Delivered",
            "CustomerCanceled": "Canceled",
            "RiderCanceled": "Canceled",
            "Failed": "Failed",
        }
        delivery_sync_status = ORDER_TO_DELIVERY_STATUS.get(new_status)
        if delivery_sync_status:
            deliveries_qs = order.deliveries.all()
            deliveries_qs.update(status=delivery_sync_status)
            if delivery_sync_status == "Delivered":
                deliveries_qs.filter(delivered_at__isnull=True).update(delivered_at=now)

        event_type, color = STATUS_MAP[new_status]
        rider_name = None
        if order.rider:
            rider_name = getattr(order.rider.user, "contact_name", None) or getattr(
                order.rider.user, "phone", None
            )

        status_labels = {
            "Started": "in transit",
            "Done": "delivered ✓",
            "CustomerCanceled": "cancelled by customer",
            "RiderCanceled": "cancelled by rider",
            "Failed": "failed",
            "Pending": "pending",
            "Assigned": "assigned",
        }
        label = status_labels.get(new_status, new_status.lower())
        if rider_name and new_status == "Started":
            text = f"{order.order_number} {label} — {rider_name} heading out"
        else:
            text = f"{order.order_number} {label}"

        emit_activity(
            event_type=event_type,
            order_id=order.order_number,
            text=text,
            color=color,
            metadata={
                "old_status": old_status,
                "new_status": new_status,
                "rider": rider_name,
            },
        )

        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=["patch"], url_path="update-price")
    def update_price(self, request, order_number=None):
        """Update the delivery fee (Order.total_amount).

        This is intentionally a dedicated endpoint because `OrderSerializer.amount`
        is read-only (computed mapping to total_amount).
        """

        order = self.get_object()

        # Guardrails: don't allow editing a paid / released order
        if getattr(order, "payment_status", None) == "Paid" or getattr(
            order, "escrow_released", False
        ):
            return Response(
                {"error": "Cannot update price for paid/released orders."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ser = self.OrderPriceUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        new_amount = ser.validated_data["amount"]

        # Capture old amount before overwriting
        old_amount = order.total_amount

        order.total_amount = new_amount
        order.save(update_fields=["total_amount", "updated_at"])

        # Record audit event
        from orders.models import OrderEvent

        OrderEvent.objects.create(
            order=order,
            event="price_change",
            description=f"Price changed from ₦{old_amount} to ₦{new_amount}",
            old_value=str(old_amount),
            new_value=str(new_amount),
            created_by=request.user if request.user.is_authenticated else None,
        )

        # If this is a relay order, recalculate leg payouts as a proportional
        # share of the new total_amount weighted by each leg's distance.
        # Formula: leg_payout = (leg_km / total_km) * total_amount
        if getattr(order, "is_relay_order", False):
            from decimal import Decimal, ROUND_HALF_UP

            legs = list(order.legs.all())
            if legs:
                total_distance = sum(float(l.distance_km or 0) for l in legs) or 0.0
                if total_distance > 0:
                    for leg in legs:
                        share = Decimal(
                            str(float(leg.distance_km or 0) / total_distance)
                        )
                        payout = (new_amount * share).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                        leg.rider_payout = payout
                        leg.save(update_fields=["rider_payout"])

        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=["patch"], url_path="update-partner-stats")
    def update_partner_stats(self, request, order_number=None):
        """Update partner-specific order stats (rider_completed_count, day_returned_count)."""
        order = self.get_object()
        
        rider_completed_count = request.data.get("rider_completed_count")
        day_returned_count = request.data.get("day_returned_count")
        
        update_fields = []
        if rider_completed_count is not None:
            order.rider_completed_count = int(rider_completed_count)
            update_fields.append("rider_completed_count")
        if day_returned_count is not None:
            order.day_returned_count = int(day_returned_count)
            update_fields.append("day_returned_count")
            
        if update_fields:
            order.save(update_fields=update_fields)
            
        return Response(self.get_serializer(order).data)

    @exception_advice()
    @action(detail=True, methods=["get"], url_path="events")
    def events(self, request, order_number=None):
        """List all events for a particular order."""
        order = self.get_object()
        events_queryset = order.events.all().order_by("-created_at")

        from .serializers import OrderEventSerializer

        serializer = OrderEventSerializer(events_queryset, many=True)

        return service_response(
            status="success",
            message="Order events retrieved successfully",
            data=serializer.data,
            status_code=200,
        )

    @action(detail=False, methods=["post"], url_path="export-history")
    def export_history(self, request):
        """Trigger an async task to export order history within a date range and email it."""
        from .tasks import export_orders_history_task

        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        if not start_date or not end_date:
            return service_response(
                status="error",
                message="Start date and end date are required",
                data={},
                status_code=400,
            )

        # Trigger Celery task
        export_orders_history_task.delay(request.user.id, start_date, end_date)

        return service_response(
            status="success",
            message="Export is being processed and will be sent to your email shortly.",
            data={},
            status_code=200,
        )

    @action(detail=True, methods=["post"], url_path="assign-relay-leg")
    def assign_relay_leg(self, request, order_number=None):
        """Assign or change the rider for a specific relay leg.
        If the sub-order has already been created, updates the sub-order too.
        """
        from orders.models import Order

        order = self.get_object()
        leg_number = request.data.get("leg_number")
        rider_id = request.data.get("rider_id")

        if not order.is_relay_order:
            return Response(
                {"error": "This order is not a relay order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        leg = order.legs.filter(leg_number=leg_number).first()
        if not leg:
            return Response(
                {"error": f"Leg {leg_number} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Retrieve the updated rider or None
        if not rider_id:
            rider = None
        else:
            try:
                rider = Rider.objects.get(rider_id=rider_id)
            except Rider.DoesNotExist:
                return Response(
                    {"error": "Rider not found"}, status=status.HTTP_404_NOT_FOUND
                )

        # Check if the sub-order already exists for this leg
        sub_order = Order.objects.filter(
            parent_order=order, relay_leg_number=leg_number
        ).first()

        if sub_order:
            # Sub-order exists! This means accept_relay_route was already called.
            # We must update the sub-order's rider and notify them.
            if not rider:
                sub_order.rider = None
                sub_order.status = "Pending"
                sub_order.save(update_fields=["rider", "status"])
                emit_activity(
                    event_type="unassigned",
                    order_id=sub_order.order_number,
                    text=f"Leg {leg_number} unassigned from {sub_order.order_number}",
                    color="yellow",
                    metadata={},
                )
                leg.rider = None
                leg.status = "Pending"
                leg.save(update_fields=["rider", "status"])
            else:
                sub_order.rider = rider
                sub_order.status = "Assigned"
                sub_order.assigned_at = timezone.now()
                sub_order.dispatcher_assigned = True
                sub_order.save(
                    update_fields=[
                        "rider",
                        "status",
                        "assigned_at",
                        "dispatcher_assigned",
                    ]
                )
                rider_name = getattr(rider.user, "contact_name", None) or getattr(
                    rider.user, "phone", "Unknown"
                )
                emit_activity(
                    event_type="assigned",
                    order_id=sub_order.order_number,
                    text=f"Leg {leg_number} assigned to {rider_name}",
                    color="blue",
                    metadata={"rider": rider_name, "rider_id": rider.rider_id},
                )
                leg.rider = rider
                leg.status = "Assigned"
                leg.assigned_at = sub_order.assigned_at
                leg.save(update_fields=["rider", "status", "assigned_at"])

                # Notify the newly assigned rider
                try:
                    from riders.notifications import notify_rider

                    notify_rider(
                        rider=rider,
                        title="Relay Leg Assigned 🔁",
                        body=f"You have been assigned Leg {leg_number} of relay order #{order.order_number}. Pick up from: {sub_order.pickup_address}.",
                        data={
                            "order_number": sub_order.order_number,
                            "status": "Assigned",
                        },
                    )
                    publish_order_assigned_event(sub_order, rider)
                except Exception as exc:
                    logger.warning(f"Relay leg assignment notification failed: {exc}")

                # Notify the merchant that a rider was assigned to a relay leg
                try:
                    merchant_profile = getattr(sub_order.merchant, "merchant_profile", None)
                    if merchant_profile:
                        send_merchant_notification.delay(
                            merchant_id=str(merchant_profile.id),
                            title="Rider Assigned 🚀",
                            body=f"Leg {leg_number} of your relay order #{order.order_number} has a rider assigned.",
                            data={
                                "order_number": sub_order.order_number,
                                "parent_order_number": order.order_number,
                                "leg_number": leg_number,
                                "status": "Assigned",
                            },
                            category="order_assigned",
                        )
                except Exception as exc:
                    logger.warning(f"Merchant relay notification failed: {exc}")
        else:
            # Sub-order not yet created. Just update the suggested rider on the leg.
            leg.suggested_rider = rider
            leg.save(update_fields=["suggested_rider"])

        # Re-fetch parent order with all relations so the serializer runs cleanly
        order = (
            Order.objects.prefetch_related(
                "legs",
                "legs__start_relay_node",
                "legs__end_relay_node",
                "legs__rider",
                "legs__rider__user",
                "legs__suggested_rider",
                "legs__suggested_rider__user",
                "sub_orders",
                "deliveries",
                "events",
                "events__created_by",
            )
            .select_related("user", "rider", "rider__user", "suggested_rider")
            .get(pk=order.pk)
        )

        return Response(self.get_serializer(order).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="accept-relay-route")
    def accept_relay_route(self, request, order_number=None):
        """Accept a generated relay route: create one sub-order per leg, assign the
        suggested rider to each, set correct pickup/delivery locations, and link
        every sub-order back to this parent order via Order.parent_order.

        The parent order's routing_status must already be READY (i.e.
        generate-relay-route has been called and succeeded).
        """
        from django.db import transaction
        from orders.models import Order, OrderLeg, Delivery

        order = self.get_object()

        # ── Guards ────────────────────────────────────────────────────────────
        if not order.is_relay_order:
            return Response(
                {"error": "This order is not a relay order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.routing_status != Order.RoutingStatus.READY:
            return Response(
                {
                    "error": (
                        f"Relay route is not ready (current status: {order.routing_status}). "
                        "Please generate the relay route first."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        legs = list(
            order.legs.select_related(
                "start_relay_node",
                "end_relay_node",
                "suggested_rider",
                "suggested_rider__user",
            ).order_by("leg_number")
        )

        if not legs:
            return Response(
                {
                    "error": "No relay legs found. Please generate the relay route first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Guard against double-acceptance: check if sub-orders already exist.
        if order.sub_orders.exists():
            return Response(
                {
                    "error": "This relay route has already been accepted and sub-orders created."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Resolve origin and final destination from parent order ─────────────
        first_delivery = order.deliveries.first()
        if not first_delivery:
            return Response(
                {"error": "Parent order has no delivery record."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Trigger the celery task asynchronously to create sub-orders
        from .tasks import process_accepted_relay_route_task

        process_accepted_relay_route_task.delay(str(order.id))

        # Re-fetch with all relations so the serializer returns the full picture.
        from orders.models import Order as OrderModel

        order = (
            OrderModel.objects.prefetch_related(
                "legs",
                "legs__start_relay_node",
                "legs__end_relay_node",
                "legs__rider",
                "legs__rider__user",
                "legs__suggested_rider",
                "legs__suggested_rider__user",
                "sub_orders",
                "deliveries",
                "events",
                "events__created_by",
            )
            .select_related("user", "rider", "rider__user", "suggested_rider")
            .get(pk=order.pk)
        )

        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)

    @exception_advice(model_object=ErrorLog)
    @action(detail=False, methods=["post"], url_path="merge-grouped-orders")
    def merge_grouped_orders(self, request):
        """Bulk merge multiple grouped orders into a parent order (Dispatcher Action)."""
        serializer = MergeGroupedOrdersSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order_ids = serializer.validated_data["order_ids"]
        # Use simple Order model here if possible or self.queryset.model
        from orders.models import Order

        orders = Order.objects.filter(order_number__in=order_ids)
        if not orders.exists():
            return Response(
                {"success": False, "message": "No valid orders found to merge"},
                status=status.HTTP_404_NOT_FOUND,
            )

        first_order = orders.first()
        total_amount = sum(o.total_amount for o in orders)

        # Create Parent Order
        parent_order = Order.objects.create(
            user=request.user,  # Dispatcher as creator
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

    @action(detail=True, methods=["post"], url_path="generate-relay-route")
    def generate_relay_route(self, request, order_number=None):
        """Synchronously generate relay legs for this order (triggered manually by dispatcher)."""
        from orders.models import Order
        from .tasks import generate_relay_legs_sync

        order = self.get_object()

        # Auto-convert non-relay orders to relay when dispatcher triggers routing
        if not getattr(order, "is_relay_order", False):
            # Geocode missing coordinates from address strings
            from orders.utils import geocode_address

            first_delivery = order.deliveries.first()

            if not order.pickup_latitude or not order.pickup_longitude:
                if order.pickup_address:
                    geo = geocode_address(order.pickup_address)
                    if geo:
                        order.pickup_latitude = geo["lat"]
                        order.pickup_longitude = geo["lng"]

            if first_delivery and (
                not first_delivery.dropoff_latitude
                or not first_delivery.dropoff_longitude
            ):
                if first_delivery.dropoff_address:
                    geo = geocode_address(first_delivery.dropoff_address)
                    if geo:
                        first_delivery.dropoff_latitude = geo["lat"]
                        first_delivery.dropoff_longitude = geo["lng"]
                        first_delivery.save(
                            update_fields=["dropoff_latitude", "dropoff_longitude"]
                        )

            # Check again after geocoding attempt
            pickup_ok = order.pickup_latitude and order.pickup_longitude
            dropoff_ok = (
                first_delivery
                and first_delivery.dropoff_latitude
                and first_delivery.dropoff_longitude
            )

            if not pickup_ok or not dropoff_ok:
                missing = []
                if not pickup_ok:
                    missing.append("pickup")
                if not dropoff_ok:
                    missing.append("dropoff")
                return Response(
                    {
                        "error": f"Could not geocode {' and '.join(missing)} address. Please check the address is valid."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            order.is_relay_order = True
            order.routing_status = Order.RoutingStatus.PENDING
            order.save(
                update_fields=[
                    "is_relay_order",
                    "routing_status",
                    "pickup_latitude",
                    "pickup_longitude",
                ]
            )

        # If already ready with legs and not a forced retry, return current state
        # if (
        #     getattr(order, "routing_status", None) == Order.RoutingStatus.READY
        #     and order.legs.exists()
        #     and not request.data.get("force", False)
        # ):
        #     serializer = self.get_serializer(order)
        #     return Response(serializer.data, status=status.HTTP_200_OK)

        emit_activity(
            event_type="relay_route_processing",
            order_id=order.order_number,
            text=f"Relay routing started for {order.order_number}",
            color="blue",
            metadata={},
        )

        # Run synchronously — blocking until legs are created or an error is set
        generate_relay_legs_sync(str(order.id))

        # Re-fetch with all needed relations so the serializer includes relay legs
        from orders.models import Order as OrderModel

        order = (
            OrderModel.objects.prefetch_related(
                "legs",
                "legs__start_relay_node",
                "legs__end_relay_node",
                "legs__suggested_rider",
                "legs__suggested_rider__user",
                "deliveries",
            )
            .select_related(
                "user", "rider", "rider__user", "rider__vehicle_type", "suggested_rider"
            )
            .get(pk=order.pk)
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MerchantAPIKeyRequestOTPView(views.APIView):
    """
    Step 1: Request an OTP to retrieve/rotate the Merchant API Key.
    JWT authenticated. OTP is sent to the merchant's registered email.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        user = request.user

        # Ensure user is a merchant of type 'api'
        merchant_profile = getattr(user, "merchant_profile", None)
        if not merchant_profile or merchant_profile.merchant_type != "api":
            raise ServiceException(
                status_code=403,
                message="Only merchants of type 'api' can request an API key.",
            )
        if merchant_profile.merchant_type != "api":
            raise ServiceException(
                status_code=403, message="Merchant must have api access! 🙈"
            )

        # Generate OTP
        otp = OTPService.generate_otp()
        print(otp)
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save(update_fields=["otp", "otp_created_at"])

        # Send OTP via Email
        try:
            OTPService.send_email_otp(user, otp)
            logger.info(f"Merchant API Key OTP sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send Merchant API Key OTP email: {str(e)}")
            raise ServiceException(
                status_code=500,
                message="Failed to send OTP email. Please try again later.",
            )

        return service_response(
            status="success",
            message="OTP sent to your registered email.",
            data={},
            status_code=200,
        )


class MerchantAPIKeyRetrieveView(views.APIView):
    """
    Step 2: Provide OTP to retrieve/rotate the Merchant API Key.
    JWT authenticated. Returns the raw API key ONLY ONCE.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        user = request.user
        otp = request.data.get("otp")

        if not otp:
            raise ServiceException(status_code=400, message="OTP is required.")

        # Ensure user is a merchant of type 'api'
        merchant_profile = getattr(user, "merchant_profile", None)
        if not merchant_profile or merchant_profile.merchant_type != "api":
            raise ServiceException(
                status_code=403,
                message="Only merchants of type 'api' can retrieve an API key.",
            )

        # Basic OTP validation (expiry - 10 minutes)
        if user.otp != otp:
            raise ServiceException(status_code=400, message="Invalid OTP.")

        expiry_time = timezone.now() - datetime.timedelta(minutes=10)
        if not user.otp_created_at or user.otp_created_at < expiry_time:
            raise ServiceException(status_code=400, message="OTP has expired.")

        # OTP is valid, clear it
        user.otp = None
        user.save(update_fields=["otp"])

        # Generate new API Key
        raw_key = f"ak_live_{secrets.token_urlsafe(32)}"
        prefix = raw_key[:11]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Update or create the API key
        MerchantAPIKey.objects.update_or_create(
            merchant=user,
            defaults={
                "key_hash": key_hash,
                "prefix": prefix,
                "is_active": True,
                "created_at": timezone.now(),
            },
        )

        return service_response(
            status="success",
            message="API Key generated successfully. Please store it securely.",
            data={"api_key": raw_key},
            status_code=200,
        )


class MerchantRequestAPIAccessView(views.APIView):
    """
    Allow a regular merchant to switch their account type to 'api'.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        user = request.user
        merchant_profile = getattr(user, "merchant_profile", None)

        if not merchant_profile:
            raise ServiceException(
                status_code=403, message="Only merchant users can request API access."
            )

        if merchant_profile.merchant_type == "api":
            return service_response(
                status="success",
                message="Account is already set to API type.",
                data={},
                status_code=200,
            )

        merchant_profile.merchant_type = "api"
        merchant_profile.save(update_fields=["merchant_type"])

        logger.info(f"Merchant {user.email} switched to API type.")

        return service_response(
            status="success",
            message="Your account has been switched to API type successfully.",
            data={},
            status_code=200,
        )

    @action(detail=True, methods=["post"], url_path="accept-relay-route")
    def accept_relay_route(self, request, order_number=None):
        """Accept a generated relay route: create one sub-order per leg, assign the
        suggested rider to each, set correct pickup/delivery locations, and link
        every sub-order back to this parent order via Order.parent_order.

        The parent order's routing_status must already be READY (i.e.
        generate-relay-route has been called and succeeded).
        """
        from django.db import transaction
        from orders.models import Order, OrderLeg, Delivery

        order = self.get_object()

        # ── Guards ────────────────────────────────────────────────────────────
        if not order.is_relay_order:
            return Response(
                {"error": "This order is not a relay order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.routing_status != Order.RoutingStatus.READY:
            return Response(
                {
                    "error": (
                        f"Relay route is not ready (current status: {order.routing_status}). "
                        "Please generate the relay route first."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        legs = list(
            order.legs.select_related(
                "start_relay_node",
                "end_relay_node",
                "suggested_rider",
                "suggested_rider__user",
            ).order_by("leg_number")
        )

        if not legs:
            return Response(
                {
                    "error": "No relay legs found. Please generate the relay route first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Guard against double-acceptance: check if sub-orders already exist.
        if order.sub_orders.exists():
            return Response(
                {
                    "error": "This relay route has already been accepted and sub-orders created."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Resolve origin and final destination from parent order ─────────────
        first_delivery = order.deliveries.first()
        if not first_delivery:
            return Response(
                {"error": "Parent order has no delivery record."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Trigger the celery task asynchronously to create sub-orders
        from .tasks import process_accepted_relay_route_task

        process_accepted_relay_route_task.delay(str(order.id))

        # Re-fetch with all relations so the serializer returns the full picture.
        from orders.models import Order as OrderModel

        order = (
            OrderModel.objects.prefetch_related(
                "legs",
                "legs__start_relay_node",
                "legs__end_relay_node",
                "legs__rider",
                "legs__rider__user",
                "legs__suggested_rider",
                "legs__suggested_rider__user",
                "sub_orders",
                "deliveries",
                "events",
                "events__created_by",
            )
            .select_related("user", "rider", "rider__user", "suggested_rider")
            .get(pk=order.pk)
        )

        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)


class ActivityFeedView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .serializers import ActivityFeedSerializer

        limit = int(request.query_params.get("limit", 50))
        limit = min(limit, 200)  # cap at 200
        entries = ActivityFeed.objects.all()[:limit]
        serializer = ActivityFeedSerializer(entries, many=True)
        return Response(serializer.data)


class AblyTokenView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        import json
        from django.conf import settings as django_settings

        api_key = getattr(django_settings, "ABLY_API_KEY", "")
        if not api_key:
            return Response(
                {"error": "Ably not configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        rider_id = None
        try:
            rider_id = request.user.rider_profile.rider_id
        except Exception:
            pass

        # Wildcard capability: covers "assigned-{any-rider-id}" and the broadcast feed.
        # Dispatchers (no rider profile) only get dispatch-feed.
        capability = {
            "dispatch-feed": ["subscribe"],
            "vehicle-telemetry": ["subscribe"],
            "assigned-*": ["subscribe"],
            "for-you": ["subscribe"],
            "for-you*": ["subscribe"],
            f"for-you-{rider_id}": ["subscribe"],
            "assigned*": ["subscribe"],
            "order*": ["subscribe"],
            "location-update": ["publish", "subscribe"],
            # Support chat channels — all parties (dispatcher + user) need pub+sub
            "chat:*": ["publish", "subscribe"],
        }

        try:
            import asyncio
            from ably import AblyRest

            async def _create_both():
                client = AblyRest(api_key)
                params = {
                    "capability": json.dumps(capability),
                    "ttl": 24 * 60 * 60 * 1000,  # 24 hours in ms (Ably max)
                }
                token_details = await client.auth.request_token(params)
                token_request = await client.auth.create_token_request(params)
                return token_details, token_request

            token_details, token_request = asyncio.run(_create_both())
            return Response(
                {
                    "token": token_details.token,
                    "token_request": token_request.to_dict(),
                }
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MerchantViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(usertype="Merchant")
    from .serializers import MerchantSerializer

    serializer_class = MerchantSerializer
    authentication_classes = [
        ServiceAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [IsDispatcherAdmin]

    def get_queryset(self):
        return super().get_queryset().order_by("-created_at")
    
    def get_permissions(self):
        if self.action == "list":
            return [IsDispatcher()]
        return super().get_permissions()

    @exception_advice(model_object=ErrorLog)
    def destroy(self, request, *args, **kwargs):
        """Soft-deactivate a merchant account."""
        instance = self.get_object()

        # Check for active orders
        active_statuses = [
            "Pending",
            "Assigned",
            "AssignmentAccepted",
            "Started",
            "Pickup",
            "Fulfilling",
            "Arrived",
        ]
        if instance.orders.filter(status__in=active_statuses).exists():
            raise ServiceException(
                status_code=400,
                message="Cannot delete merchant with active/ongoing orders.",
            )

        # Soft-deactivate user
        instance.is_active = False
        instance.save(update_fields=["is_active"])

        # Update merchant profile status
        if hasattr(instance, "merchant_profile"):
            profile = instance.merchant_profile
            profile.activity_status = "inactive"
            profile.save(update_fields=["activity_status"])

        return service_response(
            status="success",
            message=f"Merchant {instance.business_name or instance.phone} deactivated successfully.",
            data={},
            status_code=200,
        )


class MerchantPricingOverrideViewSet(viewsets.ModelViewSet):
    """CRUD (POST-upsert) for per-merchant/per-vehicle pricing overrides."""

    from orders.models import MerchantPricingOverride
    from .serializers import MerchantPricingOverrideSerializer

    queryset = MerchantPricingOverride.objects.select_related(
        "merchant", "vehicle"
    ).all()
    serializer_class = MerchantPricingOverrideSerializer
    permission_classes = [IsDispatcherAdmin]

    def get_queryset(self):
        qs = super().get_queryset().order_by("-updated_at")

        merchant = self.request.query_params.get("merchant")
        vehicle = self.request.query_params.get("vehicle")
        active = self.request.query_params.get("active")

        if merchant:
            qs = qs.filter(merchant_id=merchant)
        if vehicle:
            qs = qs.filter(vehicle_id=vehicle)
        if active is not None:
            qs = qs.filter(is_active=str(active).lower() in ("true", "1", "yes"))

        return qs


class SystemSettingsView(views.APIView):
    permission_classes = [IsDispatcherAdmin]

    def get(self, request):
        from .models import SystemSettings
        from .serializers import SystemSettingsSerializer

        settings = SystemSettings.objects.first() or SystemSettings.objects.create()
        serializer = SystemSettingsSerializer(settings)
        return Response(serializer.data)

    def post(self, request):
        from .models import SystemSettings
        from .serializers import SystemSettingsSerializer

        settings = SystemSettings.objects.first() or SystemSettings.objects.create()
        serializer = SystemSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RiderOnboardingView(views.APIView):
    permission_classes = [IsDispatcherAdmin]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        from .serializers import RiderOnboardingSerializer

        serializer = RiderOnboardingSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            rider = serializer.save()
            return Response(
                {
                    "message": "Driver onboarded successfully.",
                    "rider_id": rider.rider_id,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class S3PresignedUrlView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        import uuid
        import os
        from .s3_utils import generate_presigned_url

        filename = request.query_params.get("filename")
        folder = request.query_params.get("folder", "uploads")

        if not filename:
            return Response(
                {"error": "filename is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Generate unique object name
        file_ext = filename.split(".")[-1]
        object_name = f"{folder}/{uuid.uuid4()}.{file_ext}"

        url = generate_presigned_url(object_name)
        if url:
            bucket = os.getenv("AWS_STORAGE_BUCKET_NAME", "secourhub")
            region = os.getenv("AWS_S3_REGION_NAME", "eu-north-1")
            public_url = f"https://{bucket}.s3.{region}.amazonaws.com/{object_name}"
            return Response(
                {"url": url, "object_name": object_name, "public_url": public_url}
            )
        return Response(
            {"error": "Failed to generate presigned URL"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ZoneViewSet(viewsets.ModelViewSet):
    """CRUD for delivery zones."""

    queryset = Zone.objects.filter(is_active=True).order_by("name")
    serializer_class = ZoneSerializer
    authentication_classes = [
        ServiceAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.IsAuthenticated]


class RelayNodeViewSet(viewsets.ModelViewSet):
    """CRUD for relay nodes (handoff points)."""

    queryset = RelayNode.objects.all().select_related("zone").order_by("name")
    serializer_class = RelayNodeSerializer
    authentication_classes = [
        ServiceAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        zone_id = self.request.query_params.get("zone")
        if zone_id:
            qs = qs.filter(zone__id=zone_id)
        return qs


class DispatcherViewSet(viewsets.ViewSet):
    """List and create dispatcher users / profiles."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        from .models import DispatcherProfile
        from .serializers import DispatcherListSerializer

        qs = (
            DispatcherProfile.objects.all()
            .select_related("user")
            .order_by("-created_at")
        )
        serializer = DispatcherListSerializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request):
        from .serializers import DispatcherCreateSerializer, DispatcherListSerializer

        serializer = DispatcherCreateSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            return Response(
                DispatcherListSerializer(profile).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VehicleAssetViewSet(viewsets.ModelViewSet):
    """CRUD for physical vehicle assets."""

    queryset = VehicleAsset.objects.all().order_by("plate_number")
    serializer_class = VehicleAssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        # deliveries_km_today is a persisted model field kept up to date by the
        # compute_deliveries_today cron job.  No live annotation is needed here —
        # using a stored field means Ably real-time payloads (which also call
        # VehicleAssetSerializer) always carry the correct value.
        qs = qs.prefetch_related(
            Prefetch(
                "riders",
                queryset=Rider.objects.select_related("user").order_by("created_at"),
            )
        )

        vtype = self.request.query_params.get("type")
        if vtype:
            qs = qs.filter(vehicle_type=vtype)
        active = self.request.query_params.get("active")
        if active is not None:
            qs = qs.filter(is_active=active.lower() in ("true", "1"))
        return qs


class VerticalViewSet(viewsets.ModelViewSet):
    """Full CRUD for verticals (organizational units)."""

    queryset = Vertical.objects.all().prefetch_related("zones").order_by("code")
    serializer_class = VerticalSerializer
    authentication_classes = [
        ServiceAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.IsAuthenticated]
