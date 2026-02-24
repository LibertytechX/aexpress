from datetime import timedelta
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from django.db.models import Q
from django.db import transaction

from .serializers import (
    RiderLoginSerializer,
    RiderMeSerializer,
    DeviceRegistrationSerializer,
    UpdatePermissionsSerializer,
    DutyToggleSerializer,
    AreaDemandSerializer,
    RiderOrderSerializer,
    OrderOfferListSerializer,
)
from .models import RiderSession, RiderDevice, AreaDemand, OrderOffer, RiderCodRecord
from dispatcher.models import Rider
from orders.models import Order
from orders.permissions import IsRider
from dispatcher.utils import emit_activity


class OrderOfferListView(APIView):
    """
    API endpoint for riders to see unassigned order offers.
    Returns pending offers that haven't expired.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # now = timezone.now()
        offers = (
            OrderOffer.objects.filter(
                status="pending", rider__isnull=True
            )
            .select_related("order", "order__vehicle", "order__user")
            .prefetch_related("order__deliveries")
            .order_by("-created_at")
        )

        serializer = OrderOfferListSerializer(offers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderOfferAcceptView(APIView):
    """
    API endpoint for riders to accept an order offer.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @transaction.atomic
    def post(self, request, offer_id):
        try:
            # Get rider profile
            rider = getattr(request.user, "rider_profile", None)
            if not rider:
                return Response(
                    {
                        "success": False,
                        "message": "Authenticated user is not a driver.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Get the offer and lock it for update
            try:
                offer = OrderOffer.objects.select_for_update().get(id=offer_id)
            except (OrderOffer.DoesNotExist, ValueError):
                return Response(
                    {"success": False, "message": "Offer not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # 1. Validation
            if offer.status != "pending":
                return Response(
                    {"success": False, "message": f"Offer is already {offer.status}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            order = offer.order
            if order.status != "Pending":
                OrderOffer.objects.filter(order=order, status="pending").exclude(
                    id=offer_id
                ).update(status="accepted")
                return Response(
                    {"success": False, "message": "Order is no longer available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 2. Acceptance Phase
            offer.status = "accepted"
            offer.rider = rider
            offer.save(update_fields=["status", "rider"])

            # 3. Order Assignment
            order.rider = rider
            order.status = "Assigned"
            order.save(update_fields=["rider", "status", "updated_at"])

            # 4. COD Logic
            if order.payment_method in ["cash", "cash_on_pickup", "receiver_pays"]:
                RiderCodRecord.objects.create(
                    rider=rider,
                    order=order,
                    amount=order.total_amount,
                    status=RiderCodRecord.Status.PENDING,
                )

            # 5. Cleanup: Decline/Expire other broadcast offers for this order
            OrderOffer.objects.filter(order=order, status="pending").exclude(
                id=offer_id
            ).update(status="accepted")

            # 6. Logging/Activity
            emit_activity(
                event_type="assigned",
                order_id=order.order_number,
                text=f"Offer accepted by rider {rider.rider_id}. Order assigned.",
                color="blue",
                metadata={
                    "rider_id": str(rider.id),
                    "offer_id": str(offer.id),
                    "order_number": order.order_number,
                },
            )

            return Response(
                {
                    "success": True,
                    "message": "Offer accepted and order assigned successfully.",
                    "order_number": order.order_number,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AreaDemandListView(APIView):
    """
    API endpoint for listing area demand data.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        areas = AreaDemand.objects.all()
        serializer = AreaDemandSerializer(areas, many=True)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )


class RiderLoginView(APIView):
    """
    API endpoint for rider login.
    Follows the pattern of authentication.views.LoginView but adds rider-specific logic.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RiderLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            rider = serializer.validated_data["rider"]
            data = serializer.validated_data

            # 1. Standard user last login update
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

            # 2. Check RiderAuth specific flags (if they exist)
            try:
                auth = rider.auth
                if auth.is_locked:
                    return Response(
                        {"error": "Account locked. Try again in 30 minutes."},
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
                if not auth.is_active:
                    return Response(
                        {"error": "Account is deactivated"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                auth.reset_failed_attempts()
            except Exception:
                # If auth record doesn't exist, we skip these checks
                pass

            # 3. Generate JWT tokens (SimpleJWT)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            rider.go_offline()

            # 4. Create RiderSession
            RiderSession.objects.create(
                rider=rider,
                refresh_token=refresh_token,
                device_id=data.get("device_id", ""),
                device_name=data.get("device_name", ""),
                device_os=data.get("device_os", "android"),
                fcm_token=data.get("fcm_token", ""),
                ip_address=request.META.get("REMOTE_ADDR"),
                expires_at=timezone.now() + timedelta(days=30),
            )

            # 5. Update/Register Device
            if data.get("device_id"):
                RiderDevice.objects.update_or_create(
                    device_id=data["device_id"],
                    defaults={
                        "rider": rider,
                        "fcm_token": data.get("fcm_token", ""),
                        "platform": data.get("device_os", "android"),
                        "is_active": True,
                    },
                )

            return Response(
                {
                    "success": True,
                    "message": "Login successful!",
                    "tokens": {"access": access_token, "refresh": refresh_token},
                    "rider": RiderMeSerializer(rider).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RiderTokenRefreshView(APIView):
    """
    Custom Token Refresh View for Riders.
    Updates the RiderSession with the new refresh token if rotation is enabled.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"success": False, "message": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 1. Validate the old refresh token (checks expiration/blacklist)
            # This ensures we only proceed if the token is valid per SimpleJWT
            RefreshToken(refresh_token)

            # 2. Match with our session tracking
            session = RiderSession.objects.filter(refresh_token=refresh_token).first()

            # 3. Generate new tokens (SimpleJWT handles rotation if configured)
            # We use the standard serializer logic to stay consistent with SimpleJWT settings.
            from rest_framework_simplejwt.serializers import TokenRefreshSerializer

            serializer = TokenRefreshSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            res_data = serializer.validated_data

            new_refresh_token = res_data.get("refresh")
            new_access_token = res_data.get("access")

            # 4. Update session if we found one and rotation happened
            if session and new_refresh_token:
                session.refresh_token = new_refresh_token
                session.save(update_fields=["refresh_token", "last_used_at"])

            return Response(
                {
                    "success": True,
                    "tokens": {
                        "access": new_access_token,
                        "refresh": new_refresh_token or refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class RiderDeviceRegistrationView(APIView):
    """
    API endpoint for registering/updating rider device.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeviceRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Assuming the user has a rider_profile
                rider = request.user.rider_profile
            except Exception:
                return Response(
                    {
                        "success": False,
                        "message": "No rider profile associated with this account.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            device, created = RiderDevice.objects.update_or_create(
                device_id=serializer.validated_data["device_id"],
                defaults={
                    **serializer.validated_data,
                    "rider": rider,
                    "is_active": True,
                },
            )
            return Response(
                {
                    "success": True,
                    "message": "Device registered successfully",
                    "device_id": str(device.id),
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RiderUpdatePermissionsView(APIView):
    """
    API endpoint for updating device permissions.
    """

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        serializer = UpdatePermissionsSerializer(data=request.data)
        if serializer.is_valid():
            try:
                rider = request.user.rider_profile
            except Exception:
                return Response(
                    {
                        "success": False,
                        "message": "No rider profile associated with this account.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            device = RiderDevice.objects.filter(rider=rider, is_active=True).first()
            if not device:
                return Response(
                    {
                        "success": False,
                        "message": "No active device found for this rider.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            for field, value in serializer.validated_data.items():
                setattr(device, field, value)
            device.save()
            return Response(
                {"success": True, "message": "Permissions updated successfully"}
            )
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RiderMeView(APIView):
    """
    API endpoint for getting the authenticated rider's profile.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            rider = request.user.rider_profile
            serializer = RiderMeSerializer(rider)
            return Response(
                {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        except Rider.DoesNotExist:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class RiderToggleDutyView(APIView):
    """
    API endpoint for toggling rider duty status and updating location.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DutyToggleSerializer(data=request.data)
        if serializer.is_valid():
            try:
                rider = request.user.rider_profile
            except Exception:
                return Response(
                    {
                        "success": False,
                        "message": "No rider profile associated with this account.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update status
            request_status = serializer.validated_data["status"]
            new_status = "online" if request_status == "on_duty" else "offline"
            rider.status = new_status

            # Update location if provided
            lat = serializer.validated_data.get("latitude")
            lng = serializer.validated_data.get("longitude")

            if lat is not None and lng is not None:
                rider.current_latitude = lat
                rider.current_longitude = lng
                rider.last_location_update = timezone.now()

            rider.last_seen_at = timezone.now()
            rider.save()

            return Response(
                {
                    "status": request_status,
                    "timestamp": timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RiderOrderHistoryView(APIView):
    """
    API endpoint for rider order history.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            rider = request.user.rider_profile
        except Exception:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # History typically includes completed (Done), Failed, or Canceled orders.
        history_statuses = [
            "Done",
            "Failed",
            "CustomerCanceled",
            "RiderCanceled",
            "Assigned",
            "PickedUp",
            "Started",
        ]
        orders = Order.objects.filter(
            rider=rider, status__in=history_statuses
        ).order_by("-created_at")

        serializer = RiderOrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RiderOrderDetailView(APIView):
    """
    API endpoint for rider order detail.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        try:
            rider = request.user.rider_profile
        except Exception:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Try to get by UUID (id) or order_number
        try:
            # We allow both UUID and human-readable order number
            from uuid import UUID

            lookup_filter = Q(order_number=order_id)
            try:
                UUID(order_id)
                lookup_filter |= Q(id=order_id)
            except ValueError:
                pass

            order = Order.objects.get(lookup_filter, rider=rider)
        except (Order.DoesNotExist, ValueError):
            return Response(
                {"success": False, "message": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RiderOrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
