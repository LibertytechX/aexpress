from devs.models import ErrorLog
import asyncio
import logging
from datetime import timedelta
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from django.db.models import Q
from django.db import transaction

from wallet.corebanking_service import generate_one_time_account
from sparky_utils.response import service_response
from sparky_utils.advice import exception_advice
from sparky_utils.exceptions import ServiceException

from .serializers import (
    RiderLoginSerializer,
    RiderMeSerializer,
    DeviceRegistrationSerializer,
    UpdatePermissionsSerializer,
    DutyToggleSerializer,
    AreaDemandSerializer,
    RiderOrderSerializer,
    OrderOfferListSerializer,
    RiderEarningsStatsSerializer,
    RiderTodayTripSerializer,
    RiderWalletInfoSerializer,
    RiderTransactionSerializer,
    RiderLocationSerializer,
    RiderNotificationSerializer,
)
from orders.serializers import AssignedOrderSerializer
from .models import (
    RiderSession,
    RiderDevice,
    AreaDemand,
    OrderOffer,
    RiderCodRecord,
    RiderLocation,
    RiderNotification,
)
from wallet.models import Wallet, Transaction
from dispatcher.models import Rider
from orders.models import Order, OrderEvent
from orders.permissions import IsRider
from dispatcher.utils import emit_activity
from .notifications import notify_rider

logger = logging.getLogger(__name__)


def publish_order_assigned_event(order, rider):
    """
    Publish an Ably event to channel 'assigned-{rider_id}' with the serialized
    order payload when an order is assigned to a rider.
    """
    try:
        from django.conf import settings
        from ably import AblyRest

        api_key = getattr(settings, "ABLY_API_KEY", "")
        if not api_key:
            logger.warning(
                "publish_order_assigned_event: ABLY_API_KEY not configured, skipping publish"
            )
            return

        payload = AssignedOrderSerializer(order).data
        channel_name = f"for-you-{rider.rider_id}"

        async def _publish():
            client = AblyRest(api_key)
            channel = client.channels.get(channel_name)
            await channel.publish("order_assigned", payload)

        asyncio.run(_publish())
        logger.info(
            f"publish_order_assigned_event: published order {order.order_number} "
            f"to Ably channel '{channel_name}'."
        )
    except Exception as exc:
        logger.error(
            f"publish_order_assigned_event: Ably publish failed for order "
            f"{order.order_number}: {exc}"
        )


class OrderOfferListView(APIView):
    """
    API endpoint for riders to see unassigned order offers.
    Returns pending offers that haven't expired.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request):
        # now = timezone.now()
        offers = (
            OrderOffer.objects.filter(
                status="pending", rider__isnull=True, order__status="Pending"
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

    @exception_advice(model_object=ErrorLog)
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

            #

            # Get the offer and lock it for update
            try:
                offer = OrderOffer.objects.select_for_update().get(id=offer_id)
            except (OrderOffer.DoesNotExist, ValueError):
                return Response(
                    {"success": False, "message": "Offer not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            rider_hub = rider.hub
            zone_hubs = offer.zone.relay_nodes.all().value_list("id", flat=True)
            if rider_hub not in zone_hubs:
                return Response(
                    {"success": False, "message": "Rider is not in the zone."},
                    status=status.HTTP_403_FORBIDDEN,
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
            # order.status = "AssignmentAccepted"
            order.status = "Assigned"
            order.assigned_at = timezone.now()
            order.dispatcher_assigned = False
            order.save(
                update_fields=[
                    "rider",
                    "status",
                    "assigned_at",
                    "dispatcher_assigned",
                    "updated_at",
                ]
            )

            # 3.5 Log Event
            OrderEvent.objects.create(
                order=order,
                event="assignment_accepted",
                description=f"Rider {rider.rider_id} accepted the offer. Order status updated to AssignmentAccepted.",
                created_by=request.user,
            )

            # 4. COD Logic
            if order.collect_on_delivery:
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

            # 7. Push notification to rider
            try:
                notify_rider(
                    rider=rider,
                    title="Order Assigned 📦",
                    body=f"You've been assigned order #{order.order_number}. Head to the pickup location.",
                    data={"order_number": order.order_number, "status": "Assigned"},
                )
            except Exception as exc:
                logger.warning(f"Assignment notification failed: {exc}")

            # 8. Publish Ably event to rider-specific channel
            # publish_order_assigned_event(order, rider)

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


class RiderEarningsView(APIView):
    """
    API endpoint for rider earnings stats.
    Supports period filtering: today, week, month.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        try:
            rider = getattr(request.user, "rider_profile", None)
            if not rider:
                return Response(
                    {"success": False, "message": "Rider profile not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        period = request.query_params.get("period", "today").lower()
        now = timezone.now()

        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 1. Total earnings (from trips)
        from .models import RiderEarning, RiderCodRecord
        from django.db.models import Sum

        total_earnings = (
            RiderEarning.objects.filter(
                rider=rider, created_at__gte=start_date
            ).aggregate(Sum("net_earning"))["net_earning__sum"]
            or 0.00
        )

        # 2. Trips completed
        trips_completed = Order.objects.filter(
            rider=rider, status="Done", completed_at__gte=start_date
        ).count()

        # 3. Verified COD collected
        # Use verified recorded cod for the cod collected
        cod_collected = (
            RiderCodRecord.objects.filter(
                rider=rider,
                status=RiderCodRecord.Status.VERIFIED,
                created_at__gte=start_date,
            ).aggregate(Sum("amount"))["amount__sum"]
            or 0.00
        )

        data = {
            "total_earnings": total_earnings,
            "trips_completed": trips_completed,
            "cod_collected": cod_collected,
        }

        serializer = RiderEarningsStatsSerializer(data)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )


class RiderTodayTripsView(APIView):
    """
    API endpoint for the 'Today's Trips' list.
    Returns completed orders for today.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        try:
            rider = getattr(request.user, "rider_profile", None)
            if not rider:
                return Response(
                    {"success": False, "message": "Rider profile not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # now = timezone.now()
        # start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

        orders = (
            Order.objects.filter(rider=rider, status="Done")
            .prefetch_related("deliveries")
            .order_by("-completed_at")
        )

        serializer = RiderTodayTripSerializer(orders, many=True)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )


class RiderWalletInfoView(APIView):
    """
    API endpoint for the rider wallet info screen.
    Returns available balance and pending COD.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        try:
            rider = getattr(request.user, "rider_profile", None)
            if not rider:
                return Response(
                    {"success": False, "message": "Rider profile not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RiderWalletInfoSerializer(rider)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )


class RiderTransactionListView(APIView):
    """
    API endpoint for riders to view their wallet transaction history.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        try:
            rider = getattr(request.user, "rider_profile", None)
            if not rider:
                return Response(
                    {"success": False, "message": "Rider profile not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Ensure user has a wallet
            wallet, _ = Wallet.objects.get_or_create(user=request.user)

            # Get transactions for this wallet
            transactions = Transaction.objects.filter(wallet=wallet).order_by(
                "-created_at"
            )

            # Paginate
            from wallet.views import TransactionPagination

            paginator = TransactionPagination()
            paginated_txns = paginator.paginate_queryset(transactions, request)

            serializer = RiderTransactionSerializer(paginated_txns, many=True)
            return paginator.get_paginated_response(
                {"success": True, "data": serializer.data}
            )

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RiderLocationUpdateView(APIView):
    """
    Mobile app regularly POSTs GPS coordinates here.
    Creates or updates the single RiderLocation record for the authenticated rider
    and mirrors the coords onto the Rider master profile for fast lookups.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def post(self, request):
        serializer = RiderLocationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = serializer.validated_data

        # Upsert the dedicated location record (one row per rider)
        RiderLocation.objects.update_or_create(
            rider=rider,
            defaults={
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "accuracy": data.get("accuracy"),
                "heading": data.get("heading"),
                "speed": data.get("speed"),
            },
        )

        # Mirror onto rider profile for quick access elsewhere in the system
        rider.current_latitude = data["latitude"]
        rider.current_longitude = data["longitude"]
        rider.last_location_update = timezone.now()
        rider.save(
            update_fields=[
                "current_latitude",
                "current_longitude",
                "last_location_update",
            ]
        )

        return Response(
            {"success": True, "message": "Location updated."},
            status=status.HTTP_200_OK,
        )


class RiderNotificationListView(APIView):
    """
    API endpoint for listing rider notifications.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notifications = RiderNotification.objects.filter(rider=rider).order_by(
            "-created_at"
        )
        serializer = RiderNotificationSerializer(notifications, many=True)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )


class RiderNotificationDetailView(APIView):
    """
    API endpoint for retrieving a rider notification.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request, pk):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            notification = RiderNotification.objects.get(pk=pk, rider=rider)
        except RiderNotification.DoesNotExist:
            return Response(
                {"success": False, "message": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RiderNotificationSerializer(notification)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )


class RiderNotificationMarkReadView(APIView):
    """
    API endpoint for marking a notification as read.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def post(self, request, pk):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            notification = RiderNotification.objects.get(pk=pk, rider=rider)
            notification.is_read = True
            notification.save(update_fields=["is_read"])
            return Response(
                {"success": True, "message": "Notification marked as read."},
                status=status.HTTP_200_OK,
            )
        except RiderNotification.DoesNotExist:
            return Response(
                {"success": False, "message": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class GenerateCODAccountView(APIView):
    """
    API endpoint to generate a one-time Wema Bank account for COD remission.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def post(self, request, order_id):
        try:
            # get the order
            order = Order.objects.get(order_number=order_id)
            rider = order.rider

            cod_record = (
                RiderCodRecord.objects.filter(order=order, rider=rider)
                .order_by("-created_at")
                .first()
            )
            if not cod_record:
                return service_response(
                    status="error",
                    message="COD record not found.",
                    data={},
                    status_code=404,
                )

            if cod_record.status != RiderCodRecord.Status.PENDING:
                return service_response(
                    status="error",
                    message=f"COD record is not pending. Status is {cod_record.status}.",
                    data={},
                    status_code=400,
                )

            # Check if payment_info exists and if it's within the 30-minute window
            if cod_record.payment_info:
                from django.utils import timezone
                import datetime

                # Check when it was generated by looking at the updated_at timestamp
                # or fallback to created_at if updated_at is somehow missing
                last_updated = cod_record.updated_at or cod_record.created_at
                time_elapsed = timezone.now() - last_updated

                # If generated within the last 30 minutes, return the existing one
                if time_elapsed < datetime.timedelta(minutes=30):
                    return service_response(
                        status="success",
                        message="Payment info already exists.",
                        data=cod_record.payment_info,
                        status_code=200,
                    )
                # Otherwise, it has expired, so we will generate a new one below

            # Generate reference
            payment_ref = (
                f"COD-{cod_record.id.hex[:10].upper()}-{timezone.now().timestamp()}"
            )

            success, account_data = generate_one_time_account(payment_ref)
            if success:
                cod_record.payment_ref = payment_ref
                cod_record.payment_info = account_data
                cod_record.save(
                    update_fields=["payment_ref", "payment_info", "updated_at"]
                )

                return service_response(
                    status="success",
                    message="One-time account generated successfully.",
                    data=account_data,
                    status_code=200,
                )
            else:
                return service_response(
                    status="error",
                    message="Failed to generate one-time account.",
                    data=account_data,
                    status_code=400,
                )

        except Exception as e:
            logger.error(f"Error generating COD account: {e}", exc_info=True)
            return service_response(
                status="error",
                message=str(e),
                data={},
                status_code=500,
            )


class RiderAssignmentActionView(APIView):
    """
    API endpoint for riders to accept or reject an assignment.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice()
    def post(self, request, order_number):
        action = request.data.get("action")
        if action not in ["accept", "reject"]:
            raise ServiceException(
                status_code=400, message="Invalid action. Use 'accept' or 'reject'."
            )

        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            raise ServiceException(status_code=404, message="Order not found.")

        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            raise ServiceException(
                status_code=403, message="Authenticated user is not a driver."
            )

        if order.rider != rider:
            raise ServiceException(
                status_code=403, message="This order is not assigned to you."
            )

        if action == "accept":
            order.status = "AssignmentAccepted"
            event_msg = f"Rider {rider.rider_id} accepted the assignment."
            activity_text = f"Assignment accepted by rider {rider.rider_id}."
            notif_title = "Assignment Accepted ✅"
        else:
            order.status = "AssignmentRejected"
            order.rider = None  # Remove rider if rejected
            event_msg = f"Rider {rider.rider_id} rejected the assignment."
            activity_text = f"Assignment rejected by rider {rider.rider_id}."
            notif_title = "Assignment Rejected ❌"

        order.save(update_fields=["status", "rider", "updated_at"])

        # Log Event
        OrderEvent.objects.create(
            order=order,
            event=f"assignment_{action}ed",
            description=event_msg,
            created_by=request.user,
        )

        # Emit Activity
        emit_activity(
            event_type=f"assignment_{action}ed",
            order_id=order.order_number,
            text=activity_text,
            color="blue" if action == "accept" else "red",
            metadata={
                "rider_id": str(rider.id),
                "order_number": order.order_number,
            },
        )

        return service_response(
            status="success",
            message=f"Assignment {action}ed successfully.",
            data={"order_number": order.order_number, "status": order.status},
            status_code=200,
        )
