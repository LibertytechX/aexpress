import logging
from rest_framework import viewsets, permissions, status, views, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Rider, ActivityFeed
from .serializers import RiderSerializer
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
        return super().get_queryset().order_by("-created_at")

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
        emit_activity(
            event_type="new_order",
            order_id=order.order_number,
            text=f"New order {order.order_number} from {merchant_name}",
            color="gold",
            metadata={
                "merchant": merchant_name,
                "amount": str(order.total_amount or 0),
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
            "In Transit": "Started",
            "Delivered": "Done",
            "Cancelled": "CustomerCanceled",
            "Picked Up": "Started",  # "Picked Up" maps to Started (in transit)
        }
        new_status = DISPLAY_TO_INTERNAL.get(new_status, new_status)

        STATUS_MAP = {
            "Pending": ("new_order", "gold"),
            "Assigned": ("assigned", "blue"),
            "Started": ("in_transit", "gold"),
            "Done": ("delivered", "green"),
            "CustomerCanceled": ("cancelled", "red"),
            "RiderCanceled": ("cancelled", "red"),
            "Failed": ("failed", "red"),
        }

        if new_status not in STATUS_MAP:
            return Response(
                {"error": f"Invalid status. Choose from: {list(STATUS_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = order.status
        order.status = new_status
        order.save(update_fields=["status"])

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

        # Wildcard capability: covers "assigned-{any-rider-id}" and the broadcast feed.
        # Dispatchers (no rider profile) only get dispatch-feed.
        capability = {
            "dispatch-feed": ["subscribe"],
            "assigned-*": ["subscribe"],
            "for-you": ["subscribe"],
        }

        try:
            import asyncio
            from ably import AblyRest

            async def _create_token_req():
                client = AblyRest(api_key)
                return await client.auth.create_token_request(
                    {"capability": json.dumps(capability)}
                )

            token_request = asyncio.run(_create_token_req())
            return Response(token_request.to_dict())
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

        settings, created = SystemSettings.objects.get_or_create(id=1)
        serializer = SystemSettingsSerializer(settings)
        return Response(serializer.data)

    def post(self, request):
        from .models import SystemSettings
        from .serializers import SystemSettingsSerializer

        settings, created = SystemSettings.objects.get_or_create(id=1)
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
