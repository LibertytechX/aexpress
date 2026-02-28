import logging
from rest_framework import viewsets, permissions, status, views, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Rider, ActivityFeed, Zone, RelayNode, VehicleAsset
from .serializers import RiderSerializer, ZoneSerializer, RelayNodeSerializer, VehicleAssetSerializer
from .utils import emit_activity
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from riders.notifications import notify_rider
from riders.views import publish_order_assigned_event

logger = logging.getLogger(__name__)

User = get_user_model()


class RiderViewSet(viewsets.ModelViewSet):
    queryset = Rider.objects.all().select_related("user", "vehicle_type")
    serializer_class = RiderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Rider.objects.all().select_related("user", "vehicle_type")

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


class OrderViewSet(viewsets.ModelViewSet):
    from orders.models import Order

    queryset = (
        Order.objects.all()
        .select_related("user", "rider", "rider__user")
        .prefetch_related("deliveries")
    )
    from .serializers import OrderSerializer, OrderCreateSerializer

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return self.OrderCreateSerializer
        return self.OrderSerializer

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "order_number"

    def get_queryset(self):
        qs = super().get_queryset().order_by("-created_at")
        # Always prefetch relay legs so the list endpoint returns them too.
        # This keeps relayLegs alive through 60-second auto-refreshes.
        return qs.prefetch_related(
            "legs",
            "legs__start_relay_node",
            "legs__end_relay_node",
            "legs__rider",
            "legs__rider__user",
        )

    def create(self, request, *args, **kwargs):
        """Override create to return full OrderSerializer data after creation."""
        from rest_framework.response import Response as DRFResponse
        from rest_framework import status as drf_status

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

        # Map frontend display names → internal model values
        DISPLAY_TO_INTERNAL = {
            "In Transit":  "Started",
            "At Dropoff":  "Arrived",   # rider is at the dropoff location
            "Delivered":   "Done",
            "Cancelled":   "CustomerCanceled",
            "Picked Up":   "PickedUp",  # distinct stage; rider app uses this too
        }
        new_status = DISPLAY_TO_INTERNAL.get(new_status, new_status)

        STATUS_MAP = {
            "Pending":          ("new_order",  "gold"),
            "Assigned":         ("assigned",   "blue"),
            "PickedUp":         ("picked_up",  "blue"),
            "Started":          ("in_transit", "gold"),
            "Arrived":          ("at_dropoff", "orange"),
            "Done":             ("delivered",  "green"),
            "CustomerCanceled": ("cancelled",  "red"),
            "RiderCanceled":    ("cancelled",  "red"),
            "Failed":           ("failed",     "red"),
        }

        if new_status not in STATUS_MAP:
            return Response(
                {"error": f"Invalid status. Choose from: {list(STATUS_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = order.status
        order.status = new_status
        order.save(update_fields=["status"])

        # Keep Delivery records in sync so the serializer fallback stays consistent.
        ORDER_TO_DELIVERY_STATUS = {
            "PickedUp":         "InTransit",   # rider has picked up → delivery in transit
            "Started":          "InTransit",
            "Arrived":          "InTransit",   # rider at dropoff; delivery still in progress
            "Done":             "Delivered",
            "CustomerCanceled": "Canceled",
            "RiderCanceled":    "Canceled",
            "Failed":           "Failed",
        }
        delivery_sync_status = ORDER_TO_DELIVERY_STATUS.get(new_status)
        if delivery_sync_status:
            order.deliveries.all().update(status=delivery_sync_status)

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
        if (
            getattr(order, "routing_status", None) == Order.RoutingStatus.READY
            and order.legs.exists()
            and not request.data.get("force", False)
        ):
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

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
                "deliveries",
            )
            .select_related(
                "user", "rider", "rider__user", "rider__vehicle_type", "suggested_rider"
            )
            .get(pk=order.pk)
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
            "assigned-*": ["subscribe"],
            "for-you": ["subscribe"],
            "for-you*": ["subscribe"],
            f"for-you-{rider_id}": ["subscribe"],
            "assigned*": ["subscribe"],
            "order*": ["subscribe"],
        }

        try:
            import asyncio
            from ably import AblyRest

            async def _create_both():
                client = AblyRest(api_key)
                params = {"capability": json.dumps(capability)}
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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().order_by("-created_at")


class SystemSettingsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]
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

    queryset = Zone.objects.all().order_by("name")
    serializer_class = ZoneSerializer
    permission_classes = [permissions.IsAuthenticated]


class RelayNodeViewSet(viewsets.ModelViewSet):
    """CRUD for relay nodes (handoff points)."""

    queryset = RelayNode.objects.all().select_related("zone").order_by("name")
    serializer_class = RelayNodeSerializer
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
        vtype = self.request.query_params.get("type")
        if vtype:
            qs = qs.filter(vehicle_type=vtype)
        active = self.request.query_params.get("active")
        if active is not None:
            qs = qs.filter(is_active=active.lower() in ("true", "1"))
        return qs
