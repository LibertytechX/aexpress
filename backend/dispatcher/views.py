from rest_framework import viewsets, permissions, status, views, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Rider
from .serializers import RiderSerializer
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone

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
            rider.save(update_fields=["current_latitude", "current_longitude", "last_location_update"])
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid lat/lng values."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "id": str(rider.id),
            "rider_id": rider.rider_id,
            "current_latitude": float(rider.current_latitude),
            "current_longitude": float(rider.current_longitude),
            "last_location_update": rider.last_location_update.isoformat(),
        })


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
        response_serializer = self.OrderSerializer(
            order, context={"request": request}
        )
        return DRFResponse(
            response_serializer.data, status=drf_status.HTTP_201_CREATED
        )

    from rest_framework.decorators import action

    @action(detail=True, methods=["post"])
    def assign_rider(self, request, order_number=None):
        order = self.get_object()
        rider_id = request.data.get("rider_id")

        if not rider_id:
            # If rider_id is empty/null, it might be an unassign request
            order.rider = None
            order.status = "Pending"
            order.save()
            return Response(self.get_serializer(order).data)

        try:
            rider = Rider.objects.get(
                rider_id=rider_id
            )  # Should use correct lookup field if different
            order.rider = rider
            order.status = "Assigned"
            order.save()
            return Response(self.get_serializer(order).data)
        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider not found"}, status=status.HTTP_404_NOT_FOUND
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
