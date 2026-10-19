import traceback
import traceback
from devs.models import ErrorLog
import asyncio
import base64
import logging
from datetime import timedelta
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken

from django.db.models import Q
from django.db import transaction
from django.conf import settings
from wallet.corebanking_service import generate_one_time_account
from sparky_utils.response import service_response
from sparky_utils.advice import exception_advice
from sparky_utils.exceptions import ServiceException

from .serializers import (
    RiderLoginSerializer,
    RiderRatingSerializer,
    RiderSelfRegistrationSerializer,
    RiderAffiliationSerializer,
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
    RiderDocumentSerializer,
    RiderDocumentReuploadSerializer,
    RiderDocumentListSerializer,
    RiderDocumentDetailSerializer,
    RiderDocumentCreateSerializer,
    RiderDocumentCreateResponseSerializer,
    RiderDocumentUpdateSerializer,
    RiderDocumentUpdateResponseSerializer,
    BankListSerializer,
    VerifyAccountSerializer,
    RiderWithdrawalSerializer,
    RiderSetTransactionPinSerializer,
    RiderVerifyTransactionPinSerializer,
)
from wallet.models import (
    Bank,
    RiderPayoutTransaction,
    Wallet,
    IndependentRiderPayoutWalletPool,
    IndependentRiderPayoutWalletPoolTransaction,
)
from wallet.integrations import (
    LibertyPayAccountEnquiryService,
    WemaCoreBankingPayoutSDK,
)
from orders.serializers import AssignedOrderSerializer
from .models import (
    RiderRating,
    RiderSession,
    RiderDevice,
    AreaDemand,
    OrderOffer,
    RiderCodRecord,
    RiderLocation,
    RiderNotification,
    RiderDocument,
)
from wallet.models import Wallet, Transaction
from dispatcher.models import Rider
from orders.models import Order, OrderEvent
from orders.permissions import IsRider, IsVerifiedRider
from dispatcher.utils import emit_activity
from .notifications import notify_rider
from .tasks import finalize_rider_document_upload_task

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

    permission_classes = [permissions.IsAuthenticated, IsVerifiedRider]

    @exception_advice(model_object=ErrorLog)
    def get(self, request):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return Response(
                {
                    "success": False,
                    "message": "Authenticated user is not a driver.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not rider.is_authorized or (
            rider.is_independent_rider
            and getattr(rider, "approval_status", "") != Rider.ApprovalStatus.APPROVED
        ):
            return Response(
                {
                    "success": False,
                    "message": "Account is not verified. You cannot view order offers until approved.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        offers = (
            OrderOffer.objects.filter(
                status="pending", rider__isnull=True, order__status="Pending"
            )
            .select_related("order", "order__vehicle", "order__user")
            .prefetch_related("order__deliveries")
            .order_by("-created_at")
        )

        if rider.home_zone:
            offers = offers.filter(zone=rider.home_zone)

        serializer = OrderOfferListSerializer(offers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderOfferAcceptView(APIView):
    """
    API endpoint for riders to accept an order offer.
    """

    permission_classes = [permissions.IsAuthenticated, IsVerifiedRider]

    @exception_advice(model_object=ErrorLog)
    @transaction.atomic
    def post(self, request, offer_id):

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

        if not rider.is_authorized or (
            rider.is_independent_rider
            and getattr(rider, "approval_status", "") != Rider.ApprovalStatus.APPROVED
        ):
            return Response(
                {
                    "success": False,
                    "message": "Account is not verified. You cannot accept order offers until approved.",
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
        # Zone / Hub restriction
        if offer.zone:
            if rider.home_zone and rider.home_zone != offer.zone:
                return Response(
                    {"success": False, "message": "Rider is not in the zone."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if rider.hub:
                try:
                    zone_hubs = offer.zone.relay_nodes.all().values_list(
                        "id", flat=True
                    )
                    if rider.hub.id not in zone_hubs:
                        return Response(
                            {"success": False, "message": "Rider is not in the zone."},
                            status=status.HTTP_403_FORBIDDEN,
                        )
                except Exception as exc:
                    logger.warning(f"Error getting rider hub or zone hubs: {exc}")
                    return Response(
                        {
                            "success": False,
                            "message": "Error getting rider hub or zone hubs.",
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            if not rider.hub and not rider.home_zone:
                return Response(
                    {
                        "success": False,
                        "message": "Rider has no assigned hub or home zone.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
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


class RiderSelfRegisterView(APIView):
    """
    API endpoint for independent/freelancer rider self-registration.
    Creates the rider pending ops review (is_authorized=False) and logs them
    in immediately, following the same token/session issuance as RiderLoginView.
    """

    permission_classes = [permissions.AllowAny]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        serializer = RiderSelfRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            user, rider = result["user"], result["rider"]

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            RiderSession.objects.create(
                rider=rider,
                refresh_token=refresh_token,
                device_id=request.data.get("device_id", ""),
                device_name=request.data.get("device_name", ""),
                device_os=request.data.get("device_os", "android"),
                fcm_token=request.data.get("fcm_token", ""),
                ip_address=request.META.get("REMOTE_ADDR"),
                expires_at=timezone.now() + timedelta(days=30),
            )

            return Response(
                {
                    "success": True,
                    "message": "Registration successful! Your account is pending review.",
                    "tokens": {"access": access_token, "refresh": refresh_token},
                    "rider": RiderMeSerializer(rider).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RiderDocumentListView(APIView):
    """
    API endpoint for a rider to view their uploaded KYC documents and review status.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        documents = rider.documents.all()
        serializer = RiderDocumentSerializer(documents, many=True)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )


class RiderDocumentReuploadView(APIView):
    """
    API endpoint for a rider to re-upload a document that an admin rejected.
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
            document = RiderDocument.objects.get(pk=pk, rider=rider)
        except RiderDocument.DoesNotExist:
            return Response(
                {"success": False, "message": "Document not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if document.status != RiderDocument.Status.REJECTED:
            return Response(
                {
                    "success": False,
                    "message": "Only rejected documents can be re-uploaded.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # update the rider aproval status
        rider.approval_status = Rider.ApprovalStatus.PENDING
        rider.save()

        serializer = RiderDocumentReuploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.file_url = serializer.validated_data["url"]
        document.status = RiderDocument.Status.PENDING
        document.rejection_reason = ""
        document.save(
            update_fields=["file_url", "status", "rejection_reason", "updated_at"]
        )

        return Response(
            {
                "success": True,
                "message": "Document re-uploaded successfully. Pending review.",
                "data": RiderDocumentSerializer(document).data,
            },
            status=status.HTTP_200_OK,
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


class RiderAffiliationView(APIView):
    """
    API endpoint for getting and updating rider affiliation with a dispatcher/hub captain.
    GET /api/riders/affiliation/ -> Returns current affiliation status and dispatcher details
    POST /api/riders/affiliation/ -> Affiliates rider using an affiliation code
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @exception_advice(model_object=ErrorLog)
    def get(self, request):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return service_response(
                status="error",
                message="Rider profile not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        dispatcher_data = None
        if rider.is_affiliated and rider.affiliated_to:
            disp = rider.affiliated_to
            dispatcher_data = {
                "id": str(disp.id),
                "name": (
                    disp.user.contact_name
                    or f"{disp.user.first_name} {disp.user.last_name}".strip()
                    or disp.user.phone
                ),
                "phone": disp.user.phone,
                "role": disp.get_role_display(),
                "affiliation_code": disp.affiliation_code,
            }

        return service_response(
            status="success",
            message="Rider affiliation details retrieved successfully.",
            data={
                "is_affiliated": rider.is_affiliated,
                "affiliated_at": (
                    rider.affiliated_at.isoformat() if rider.affiliated_at else None
                ),
                "dispatcher": dispatcher_data,
            },
            status_code=status.HTTP_200_OK,
        )

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return service_response(
                status="error",
                message="Rider profile not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = RiderAffiliationSerializer(data=request.data)
        if not serializer.is_valid():
            first_err = (
                next(iter(serializer.errors.values()))[0]
                if serializer.errors
                else "Invalid data."
            )
            raise ServiceException(
                status_code=status.HTTP_400_BAD_REQUEST, message=str(first_err)
            )

        code = serializer.validated_data["affiliation_code"]
        from dispatcher.services import affiliate_rider_to_dispatcher

        dispatcher = affiliate_rider_to_dispatcher(rider, code)

        dispatcher_data = {
            "id": str(dispatcher.id),
            "name": (
                dispatcher.user.contact_name
                or f"{dispatcher.user.first_name} {dispatcher.user.last_name}".strip()
                or dispatcher.user.phone
            ),
            "phone": dispatcher.user.phone,
            "role": dispatcher.get_role_display(),
            "affiliation_code": dispatcher.affiliation_code,
        }

        return service_response(
            status="success",
            message="Successfully affiliated with dispatcher.",
            data={
                "is_affiliated": True,
                "affiliated_at": (
                    rider.affiliated_at.isoformat() if rider.affiliated_at else None
                ),
                "dispatcher": dispatcher_data,
            },
            status_code=status.HTTP_200_OK,
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
            if request_status in ["on_duty", "online"]:
                if not rider.is_authorized or (
                    rider.is_independent_rider
                    and getattr(rider, "approval_status", "")
                    != Rider.ApprovalStatus.APPROVED
                ):
                    return Response(
                        {
                            "success": False,
                            "message": "Account is not verified or authorized to go online.",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            new_status = (
                "online" if request_status in ["on_duty", "online"] else "offline"
            )
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
                    "success": True,
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

    @exception_advice(model_object=ErrorLog)
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
    Supports period filtering: today (default), week, month.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
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

        orders = (
            Order.objects.filter(
                rider=rider, status="Done", completed_at__gte=start_date
            )
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

    @exception_advice(model_object=ErrorLog)
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


class RiderDocumentListCreateView(APIView):
    """
    API endpoint for listing a rider's KYC documents and uploading new ones.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        documents = RiderDocument.objects.filter(rider=rider)

        doc_type = request.query_params.get("doc_type")
        if doc_type:
            documents = documents.filter(doc_type=doc_type)

        doc_status = request.query_params.get("status")
        if doc_status:
            documents = documents.filter(status=doc_status)

        serializer = RiderDocumentListSerializer(documents, many=True)
        return Response(
            {"success": True, "message": "", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RiderDocumentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid input.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        doc_type = data["doc_type"]

        if RiderDocument.objects.filter(
            rider=rider,
            doc_type=doc_type,
            status__in=[RiderDocument.Status.PENDING, RiderDocument.Status.APPROVED],
        ).exists():
            return Response(
                {
                    "success": False,
                    "message": (
                        f"A {doc_type} document is already pending review or approved. "
                        "Update the existing document instead of creating a new one."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_obj = data["file"]
        file_data = base64.b64encode(file_obj.read()).decode("utf-8")

        # Created immediately with an empty file_url — the background task fills
        # it in once the S3 upload completes, so the view doesn't wait on it.
        document = RiderDocument.objects.create(
            rider=rider,
            doc_type=doc_type,
            file_url="",
            expires_at=data.get("expires_at"),
        )

        finalize_rider_document_upload_task.delay(
            str(document.id), file_data, file_obj.name
        )

        response_serializer = RiderDocumentCreateResponseSerializer(document)
        return Response(
            {
                "success": True,
                "message": "Document received and is being uploaded. It will be available shortly.",
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class RiderDocumentDetailView(APIView):
    """
    API endpoint for retrieving, updating, or deleting a single rider KYC document.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]
    parser_classes = [MultiPartParser, FormParser]

    def _get_document(self, request, pk):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            return None, Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            document = RiderDocument.objects.get(pk=pk, rider=rider)
        except RiderDocument.DoesNotExist:
            return None, Response(
                {"success": False, "message": "Document not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return document, None

    def get(self, request, pk):
        document, error = self._get_document(request, pk)
        if error:
            return error

        serializer = RiderDocumentDetailSerializer(document)
        return Response(
            {"success": True, "message": "", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    @exception_advice(model_object=ErrorLog)
    def patch(self, request, pk):
        document, error = self._get_document(request, pk)
        if error:
            return error

        if document.status == RiderDocument.Status.APPROVED:
            return Response(
                {"success": False, "message": "Approved documents cannot be modified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RiderDocumentUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid input.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        update_fields = []

        file_obj = data.get("file")
        file_data = None
        if file_obj:
            file_data = base64.b64encode(file_obj.read()).decode("utf-8")
            # Metadata resets immediately; the actual file_url update happens
            # in the background task once the S3 upload completes.
            document.status = RiderDocument.Status.PENDING
            document.rejection_reason = ""
            update_fields += ["status", "rejection_reason"]

        if "expires_at" in data:
            document.expires_at = data["expires_at"]
            update_fields.append("expires_at")

        if update_fields:
            update_fields.append("updated_at")
            document.save(update_fields=update_fields)

        if file_obj:
            finalize_rider_document_upload_task.delay(
                str(document.id), file_data, file_obj.name
            )

        response_serializer = RiderDocumentUpdateResponseSerializer(document)
        message = (
            "Document received and is being uploaded. It will be available shortly."
            if file_obj
            else "Document updated successfully."
        )
        return Response(
            {
                "success": True,
                "message": message,
                "data": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        document, error = self._get_document(request, pk)
        if error:
            return error

        if document.status == RiderDocument.Status.APPROVED:
            return Response(
                {"success": False, "message": "Approved documents cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.delete()
        return Response(
            {
                "success": True,
                "message": "Document deleted successfully.",
                "data": None,
            },
            status=status.HTTP_200_OK,
        )


class CustomerRatesRiderAPIView(APIView):
    """
    API endpoint for customers to rate a rider after order completion.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        serializer = RiderRatingSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.validated_data.get("comment", "")
            rating_value = serializer.validated_data["rating"]
            rider_code = serializer.validated_data["rider_code"]

            try:
                rider = Rider.objects.get(rider_id=rider_code)

            except Rider.DoesNotExist:
                return Response(
                    {"success": False, "message": "Rider not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            customer_rating = RiderRating.objects.create(
                rider=rider,
                customer=request.user,
                rating=rating_value,
                comment=comment,
            )

            rider.update_rider_average_rating()

            return Response(
                {
                    "success": True,
                    "message": "Rider rated successfully.",
                    "data": {
                        "rider_code": str(rider.id),
                        "rating": customer_rating.rating,
                        "comment": customer_rating.comment,
                    },
                },
                status=status.HTTP_200_OK,
            )

        else:
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RiderBankListView(APIView):
    """
    Public API endpoint to list all supported Nigerian banks.
    Open/Unauthenticated as requested.
    """

    permission_classes = [permissions.AllowAny]

    @exception_advice(model_object=ErrorLog)
    def get(self, request):
        banks = Bank.get_all_bank_list()
        serializer = BankListSerializer(banks, many=True)
        return service_response(
            status="success",
            message="Banks retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class RiderVerifyAccountView(APIView):
    """
    API endpoint to verify bank account number and bank code via LibertyPay Account Enquiry.
    """

    permission_classes = [permissions.AllowAny]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        serializer = VerifyAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account_number = serializer.validated_data["account_number"]
        bank_code = serializer.validated_data["bank_code"]

        enquiry_service = LibertyPayAccountEnquiryService()
        result = enquiry_service.verify_account(
            account_number=account_number, bank_code=bank_code
        )

        if not result:
            raise ServiceException(
                status_code=400,
                message="Account verification failed. Please check the account number and bank code.",
            )

        return service_response(
            status="success",
            message="Account verified successfully.",
            data=result,
            status_code=status.HTTP_200_OK,
        )


class RiderWithdrawalView(APIView):
    """
    API endpoint for independent riders to withdraw earnings to an external bank account
    via Wema CoreBanking payout.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        import uuid
        from decimal import Decimal
        from django.db.models import Sum

        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            raise ServiceException(status_code=404, message="Rider profile not found.")

        if not rider.is_independent_rider:
            raise ServiceException(
                status_code=403,
                message="Only independent riders are permitted to withdraw wallet earnings.",
            )

        request_data = (
            request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        )
        if "is_sandbox" not in request_data and "mode" not in request_data:
            query_sandbox = request.query_params.get(
                "sandbox"
            ) or request.query_params.get("is_sandbox")
            query_mode = request.query_params.get("mode")
            if query_sandbox is not None:
                request_data["is_sandbox"] = str(query_sandbox).lower() in (
                    "true",
                    "1",
                    "yes",
                )
            elif query_mode:
                request_data["mode"] = query_mode

        serializer = RiderWithdrawalSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        amount = Decimal(str(serializer.validated_data["amount"]))
        account_number = serializer.validated_data["account_number"]
        account_name = serializer.validated_data["account_name"]
        bank_code = serializer.validated_data["bank_code"]
        bank_name = serializer.validated_data.get("bank_name", "")
        narration = (
            serializer.validated_data.get("narration")
            or f"Earnings withdrawal by {rider.rider_id}"
        )
        pin = serializer.validated_data["pin"]
        if not rider.has_transaction_pin:
            raise ServiceException(
                status_code=400,
                message="Transaction PIN has not been set. Please set your transaction PIN before withdrawing.",
            )
        if not rider.check_transaction_pin(pin):
            raise ServiceException(
                status_code=400,
                message="Invalid transaction PIN. Please enter the correct PIN.",
            )

        is_sandbox = serializer.validated_data.get("is_sandbox")
        mode = serializer.validated_data.get("mode")
        if is_sandbox is None or mode is None:
            service_mode = getattr(settings, "WIHDRAWAL_MODE", "SANDBOX").upper()
            is_sandbox = (service_mode == "SANDBOX")
            mode = "SANDBOX" if is_sandbox else "LIVE"

        # Double-entry balance verification & atomic wallet and pool debit
        ref_prefix = "WDR-SBX" if is_sandbox else "WDR"
        reference = (
            f"{ref_prefix}-{uuid.uuid4().hex[:10 if is_sandbox else 12].upper()}"
        )

        with transaction.atomic():
            # 1. Check Independent Rider Payout Wallet Pool funds first
            pool = (
                IndependentRiderPayoutWalletPool.objects.select_for_update()
                .filter(is_active=True)
                .first()
            )
            if not pool:
                pool = IndependentRiderPayoutWalletPool.get_default_pool()
                pool = IndependentRiderPayoutWalletPool.objects.select_for_update().get(
                    id=pool.id
                )

            # In sandbox mode, ensure the company payout pool has sufficient test liquidity
            if is_sandbox and pool.balance < amount:
                pool.credit(
                    amount=Decimal("1000000.00"),
                    description="Sandbox automatic liquidity provision for payout testing",
                    reference=f"POOL-SBX-FUND-{uuid.uuid4().hex[:8].upper()}",
                    metadata={"sandbox": True, "auto_funded": True},
                )
                pool.refresh_from_db()

            if pool.balance < amount:
                raise ServiceException(
                    status_code=400,
                    message="Insufficient funds in payout pool. Unable to process withdrawal at this time.",
                )

            # 2. Check rider's withdrawable balance (pending unremitted COD deduction)
            wallet, _ = Wallet.objects.select_for_update().get_or_create(
                user=request.user
            )

            pending_cod_agg = rider.cod_records.filter(status="pending").aggregate(
                Sum("amount")
            )["amount__sum"]
            pending_cod = Decimal(str(pending_cod_agg or "0.00"))
            withdrawable_balance = max(wallet.balance - pending_cod, Decimal("0.00"))

            if amount > withdrawable_balance:
                raise ServiceException(
                    status_code=400,
                    message=(
                        f"Insufficient withdrawable balance. Withdrawable: ₦{withdrawable_balance:,.2f} "
                        f"(Pending unremitted COD: ₦{pending_cod:,.2f})"
                    ),
                )

            # 3. Create pending RiderPayoutTransaction
            payout = RiderPayoutTransaction.objects.create(
                rider=rider,
                pool=pool,
                destination_account_name=account_name,
                destination_account_number=account_number,
                destination_bank_code=bank_code,
                destination_bank_name=bank_name,
                amount=amount,
                reference=reference,
                narration=narration,
                status=RiderPayoutTransaction.Status.PENDING,
                mode=mode,
                is_sandbox=is_sandbox,
            )

            # 4. Debit the payout pool and record pool debit transaction
            pool.debit(
                amount=amount,
                reference=f"POOL-{reference}",
                rider=rider,
                payout_transaction=payout,
                description=f"Payout disbursement to {account_name} ({account_number}){' [Sandbox]' if is_sandbox else ''}",
                metadata={
                    "withdrawal_reference": reference,
                    "account_number": account_number,
                    "account_name": account_name,
                    "bank_code": bank_code,
                    "bank_name": bank_name,
                    "type": "rider_withdrawal_pool_debit",
                    "mode": mode,
                    "is_sandbox": is_sandbox,
                },
            )

            # 5. Debit the rider wallet and record wallet debit transaction
            wallet.debit(
                amount=amount,
                description=f"Withdrawal to {account_name} ({account_number}){' [Sandbox]' if is_sandbox else ''}",
                reference=reference,
                metadata={
                    "account_number": account_number,
                    "account_name": account_name,
                    "bank_code": bank_code,
                    "bank_name": bank_name,
                    "type": "rider_withdrawal",
                    "mode": mode,
                    "is_sandbox": is_sandbox,
                },
            )

        # Dispatch payout: do NOT hit Wema CoreBanking when in sandbox mode
        if is_sandbox or mode == "SANDBOX":
            logger.info(
                f"[SANDBOX] Bypassing external CoreBanking payout for ₦{amount} to {account_number} ({bank_code}) ref={reference}"
            )
            success = True
            resp = {
                "status": "success",
                "message": "Sandbox payout transfer simulated successfully.",
                "reference": reference,
                "request_reference": reference,
                "amount": float(amount),
                "account_name": account_name,
                "account_number": str(account_number).strip(),
                "bank_code": str(bank_code).strip(),
                "mode": "SANDBOX",
                "simulated": True,
            }
        else:
            try:
                sdk = WemaCoreBankingPayoutSDK(mode=mode)
                success, resp = sdk.transfer_funds(
                    amount=float(amount),
                    narration=narration,
                    account_name=account_name,
                    account_number=account_number,
                    bank_code=bank_code,
                    reference=reference,
                )
            except Exception as exc:
                logger.error(
                    f"Unexpected exception during CoreBanking payout transfer: {exc}"
                )
                success = False
                resp = {
                    "error": str(exc),
                    "message": "Payout transfer encountered an unexpected connection error.",
                }

        if success:
            payout.status = RiderPayoutTransaction.Status.SUCCESS
            payout.corebanking_response = resp
            payout.save(update_fields=["status", "corebanking_response", "updated_at"])

            # Save rider preferred bank details for future withdrawals
            rider.bank_name = bank_name or rider.bank_name
            rider.bank_account_number = account_number
            rider.bank_routing_code = bank_code
            rider.save(
                update_fields=["bank_name", "bank_account_number", "bank_routing_code"]
            )

            wallet.refresh_from_db()

            return service_response(
                status="success",
                message=(
                    "Withdrawal request processed successfully."
                    if not is_sandbox
                    else "[Sandbox] Withdrawal request processed successfully."
                ),
                data={
                    "reference": reference,
                    "amount": float(amount),
                    "account_number": account_number,
                    "account_name": account_name,
                    "bank_code": bank_code,
                    "status": "success",
                    "remaining_balance": float(wallet.balance),
                    "is_sandbox": is_sandbox,
                    "mode": mode,
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            # Immediate automated refund for BOTH rider wallet and payout pool
            with transaction.atomic():
                # 1. Refund rider wallet
                refund_ref = f"REF-{uuid.uuid4().hex[:12].upper()}"
                wallet.credit(
                    amount=amount,
                    description=f"Refund for failed payout {reference}",
                    reference=refund_ref,
                    metadata={
                        "original_reference": reference,
                        "reason": "CoreBanking payout rejected",
                        "mode": mode,
                        "is_sandbox": is_sandbox,
                    },
                )

                # 2. Refund payout pool
                pool_refund_ref = f"POOL-REF-{uuid.uuid4().hex[:12].upper()}"
                target_pool = (
                    payout.pool or IndependentRiderPayoutWalletPool.get_default_pool()
                )
                target_pool.credit(
                    amount=amount,
                    reference=pool_refund_ref,
                    rider=rider,
                    payout_transaction=payout,
                    description=f"Refund for failed payout {reference}",
                    metadata={
                        "original_reference": reference,
                        "reason": "CoreBanking payout rejected",
                        "mode": mode,
                        "is_sandbox": is_sandbox,
                    },
                )

                payout.status = RiderPayoutTransaction.Status.FAILED
                payout.refunded = True
                payout.corebanking_response = resp
                payout.save(
                    update_fields=[
                        "status",
                        "refunded",
                        "corebanking_response",
                        "updated_at",
                    ]
                )

            err_msg = (
                resp.get("message")
                or resp.get("error")
                or "Payout transfer could not be completed."
            )
            raise ServiceException(
                status_code=422,
                message=f"{err_msg} Your wallet balance has been refunded.",
            )


class RiderSetTransactionPinView(APIView):
    """
    API endpoint for riders to set, change, or check the status of their 4-digit transaction PIN.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
    def get(self, request):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            raise ServiceException(status_code=404, message="Rider profile not found.")

        return service_response(
            status="success",
            message="Transaction PIN status retrieved successfully.",
            data={"has_transaction_pin": rider.has_transaction_pin},
            status_code=200,
        )

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            raise ServiceException(status_code=404, message="Rider profile not found.")

        serializer = RiderSetTransactionPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_pin = serializer.validated_data["pin"]
        old_pin = serializer.validated_data.get("old_pin", "").strip()
        password = serializer.validated_data.get("password", "").strip()

        is_update = rider.has_transaction_pin
        if is_update:
            if not old_pin and not password:
                raise ServiceException(
                    status_code=400,
                    message="Current transaction PIN or account password is required to change PIN.",
                )
            if old_pin and not rider.check_transaction_pin(old_pin):
                raise ServiceException(
                    status_code=400,
                    message="Incorrect current transaction PIN.",
                )
            elif not old_pin and password:
                if not request.user.check_password(password):
                    raise ServiceException(
                        status_code=400,
                        message="Incorrect account password.",
                    )

        rider.set_transaction_pin(new_pin)
        action_msg = "updated" if is_update else "set"
        return service_response(
            status="success",
            message=f"Transaction PIN {action_msg} successfully.",
            data={"has_transaction_pin": True},
            status_code=200,
        )


class RiderVerifyTransactionPinView(APIView):
    """
    API endpoint for verifying a rider's 4-digit transaction PIN.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        rider = getattr(request.user, "rider_profile", None)
        if not rider:
            raise ServiceException(status_code=404, message="Rider profile not found.")

        if not rider.has_transaction_pin:
            raise ServiceException(
                status_code=400,
                message="Transaction PIN has not been set. Please set your transaction PIN before withdrawing.",
            )

        serializer = RiderVerifyTransactionPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pin = serializer.validated_data["pin"]
        if not rider.check_transaction_pin(pin):
            raise ServiceException(
                status_code=400,
                message="Invalid transaction PIN. Please enter the correct PIN.",
            )

        return service_response(
            status="success",
            message="Transaction PIN verified successfully.",
            data={"valid": True},
            status_code=200,
        )
