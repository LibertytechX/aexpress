from sparky_utils.exceptions import ServiceException
import re

from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from dispatcher.models import Rider
from authentication.models import User
from wallet.models import Wallet, Transaction
from .models import (
    RiderAuth,
    RiderDevice,
    RiderCodRecord,
    RiderDocument,
    OrderOffer,
    AreaDemand,
    RiderEarning,
    RiderNotification,
    RiderFaceMatchLog,
)
from orders.models import Order
from orders.serializers import AssignedOrderSerializer


class AreaDemandSerializer(serializers.ModelSerializer):
    """
    Serializer for AreaDemand model.
    """

    class Meta:
        model = AreaDemand
        fields = [
            "id",
            "area_name",
            "level",
            "pending_orders",
            "active_riders",
            "latitude",
            "longitude",
            "updated_at",
        ]


class RiderMeSerializer(serializers.ModelSerializer):
    """
    Basic rider profile data for mobile app.
    Pulling contact info from the linked User model.
    """

    firstName = serializers.CharField(source="user.first_name", read_only=True)
    lastName = serializers.CharField(source="user.last_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    wallet_balance = serializers.SerializerMethodField()
    pending_cod = serializers.SerializerMethodField()
    acceptance_rate = serializers.SerializerMethodField()
    on_time_rate = serializers.SerializerMethodField()
    documents_status = serializers.SerializerMethodField()
    net_earnings = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    face_verification_channel = serializers.SerializerMethodField()
    affiliated_to_code = serializers.SerializerMethodField()
    affiliated_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Rider
        fields = [
            "id",
            "rider_id",
            "status",
            "firstName",
            "is_independent_rider",
            "lastName",
            "phone",
            "email",
            "emergency_contact_name",
            "emergency_phone",
            "vehicle_model",
            "vehicle_plate_number",
            "rating",
            "total_deliveries",
            "wallet_balance",
            "pending_cod",
            "acceptance_rate",
            "on_time_rate",
            "documents_status",
            "net_earnings",
            "is_verified",
            "face_verification_channel",
            "face_verification_required",
            "last_face_verified_at",
            "is_affiliated",
            "affiliated_to_code",
            "affiliated_to_name",
            "affiliated_at",
        ]

    def get_affiliated_to_code(self, obj):
        if obj.affiliated_to:
            return obj.affiliated_to.affiliation_code
        return None

    def get_affiliated_to_name(self, obj):
        if obj.affiliated_to and obj.affiliated_to.user:
            return (
                obj.affiliated_to.user.contact_name
                or f"{obj.affiliated_to.user.first_name} {obj.affiliated_to.user.last_name}".strip()
                or obj.affiliated_to.user.phone
            )
        return None

    def get_is_verified(self, obj):
        if (
            obj.is_independent_rider
            and obj.is_authorized
            and not getattr(obj, "face_verification_required", False)
        ):
            return True
        elif not obj.is_independent_rider:
            return True
        else:
            return False

    def get_face_verification_channel(self, obj):
        if getattr(obj, "is_independent_rider", False):
            return f"facematch:{obj.rider_id or obj.id}"
        return None

    def get_wallet_balance(self, obj):
        try:
            return obj.user.wallet.balance
        except (AttributeError, Wallet.DoesNotExist):
            return 0.00

    def get_pending_cod(self, obj):
        # Sum of pending COD records
        total = obj.cod_records.filter(status="pending").aggregate(Sum("amount"))[
            "amount__sum"
        ]
        return total or 0.00

    def get_net_earnings(self, obj):
        total = obj.earnings.aggregate(Sum("net_earning"))["net_earning__sum"]
        return total or 0.00

    def get_acceptance_rate(self, obj):
        total_offers = obj.order_offers.count()
        if total_offers == 0:
            return 100.0
        accepted_offers = obj.order_offers.filter(status="accepted").count()
        return round((accepted_offers / total_offers) * 100, 1)

    def get_on_time_rate(self, obj):
        # Placeholder for now as we don't have explicit historical on-time data
        return 100.0

    def get_documents_status(self, obj):
        docs = obj.documents.all()
        return {
            "total": docs.count(),
            "approved": docs.filter(status="approved").count(),
            "pending": docs.filter(status="pending").count(),
            "expiring_soon": docs.filter(
                status="approved",
                expires_at__lte=timezone.now().date() + timezone.timedelta(days=30),
            ).count(),
        }


class DeviceRegistrationSerializer(serializers.ModelSerializer):
    """PermissionsScreen: register device + permissions"""

    class Meta:
        model = RiderDevice
        fields = [
            "device_id",
            "fcm_token",
            "platform",
            "model_name",
            "os_version",
            "app_version",
            "location_permission",
            "camera_permission",
            "notification_permission",
            "battery_optimization",
        ]


class UpdatePermissionsSerializer(serializers.Serializer):
    location_permission = serializers.CharField(required=False)
    camera_permission = serializers.CharField(required=False)
    notification_permission = serializers.CharField(required=False)
    battery_optimization = serializers.CharField(required=False)


class DutyToggleSerializer(serializers.Serializer):
    """
    Serializer for toggling rider duty status.
    """

    status = serializers.ChoiceField(
        choices=["on_duty", "off_duty", "online", "offline"]
    )
    latitude = serializers.DecimalField(
        max_digits=30, decimal_places=20, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=30, decimal_places=20, required=False, allow_null=True
    )


class RiderLoginSerializer(serializers.Serializer):
    """
    Serializer for rider login.
    Leverages Django authenticate() and includes device tracking fields.
    """

    phone = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    device_id = serializers.CharField(max_length=255, required=False, default="")
    device_name = serializers.CharField(max_length=255, required=False, default="")
    device_os = serializers.CharField(max_length=50, required=False, default="android")
    fcm_token = serializers.CharField(max_length=500, required=False, default="")

    def validate(self, data):
        phone = data.get("phone", "").replace(" ", "").replace("-", "")
        password = data.get("password")

        if not phone or not password:
            raise serializers.ValidationError("Phone and password are required.")

        # Try to get the user
        # should try phone number combos
        phone_2, phone_3 = "", ""
        phone_numbers = [phone]
        if phone.startswith("0"):
            phone_2 = "+234" + phone[1:]
            phone_3 = phone[1:]
            phone_numbers.append(phone_2)
            phone_numbers.append(phone_3)
        elif len(phone) == 10:
            phone_3 = "0" + phone
            phone_2 = "+234" + phone
            phone_numbers.append(phone_2)
            phone_numbers.append(phone_3)
        elif phone.startswith("+234"):
            phone_2 = phone[4:]
            phone_3 = "0" + phone_2
            phone_numbers.append(phone_2)
            phone_numbers.append(phone_3)
        print("Let's see the phone numbers: ", phone_numbers)
        user = User.objects.filter(phone__in=phone_numbers)
        if user.count() == 0:
            raise ServiceException(
                status_code=400, message="Invalid phone number or password."
            )

        user = None
        # try authentication for phone with the given password
        for phone_number in phone_numbers:
            user = authenticate(username=phone_number, password=password)
            if user:
                if not user.is_active:
                    raise ServiceException(
                        status_code=400, message="This account has been deactivated."
                    )
                break
        if not user:
            raise ServiceException(
                status_code=400, message="Invalid phone number or password."
            )

        # Ensure user has a rider profile
        try:
            rider = user.rider_profile
        except Rider.DoesNotExist:
            raise serializers.ValidationError(
                "No rider profile associated with this account."
            )

        data["rider"] = rider
        data["user"] = user
        return data


NIGERIA_PHONE_REGEX = re.compile(r"^\+234[789]\d{9}$")

REQUIRED_DOC_TYPES = {
    RiderDocument.DocType.NATIONAL_ID,
    RiderDocument.DocType.RIDERS_CARD,
    RiderDocument.DocType.DRIVERS_LICENSE,
    RiderDocument.DocType.UTILITY_BILL,
    RiderDocument.DocType.PROFILE_PHOTO,
}


class RiderDocumentInputSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=RiderDocument.DocType.choices)
    url = serializers.URLField()


class RiderSelfRegistrationSerializer(serializers.Serializer):
    """
    Serializer for independent/freelancer rider self-registration.
    Creates a User + Rider (working_type="freelancer", is_independent_rider=True,
    is_authorized=False pending ops review) plus the submitted KYC documents.
    """

    phone = serializers.CharField(required=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=6,
        style={"input_type": "password"},
    )
    confirm_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    address = serializers.CharField(required=True)
    emergency_contact_name = serializers.CharField(required=True, max_length=100)
    emergency_phone = serializers.CharField(required=True)
    bvn = serializers.RegexField(regex=r"^\d{11}$", required=True)
    vehicle_model = serializers.CharField(required=True)
    vehicle_plate_number = serializers.CharField(required=True)
    vehicle_color = serializers.CharField(required=True)
    vehicle_photo = serializers.URLField(required=True)
    rider_documents = RiderDocumentInputSerializer(many=True, required=True)
    affiliation_code = serializers.CharField(
        required=False, allow_blank=True, max_length=100
    )

    def validate_phone(self, value):
        phone = re.sub(r"[\s\-()]", "", value)

        if phone.startswith("0") and len(phone) == 11:
            phone = "+234" + phone[1:]
        elif phone.startswith("234"):
            phone = "+" + phone

        if not NIGERIA_PHONE_REGEX.match(phone):
            raise serializers.ValidationError(
                "Enter a valid Nigerian phone number, e.g. 08012345678 or +2348012345678."
            )

        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError(
                "This phone number is already registered."
            )
        return phone

    def validate_emergency_phone(self, value):
        phone = re.sub(r"[\s\-()]", "", value)

        if phone.startswith("0") and len(phone) == 11:
            phone = "+234" + phone[1:]
        elif phone.startswith("234"):
            phone = "+" + phone

        if not NIGERIA_PHONE_REGEX.match(phone):
            raise serializers.ValidationError(
                "Enter a valid Nigerian phone number for emergency contact, e.g. 08012345678 or +2348012345678."
            )
        return phone

    def validate_email(self, value):
        if not value:
            return value
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_rider_documents(self, value):
        submitted_types = {doc["type"] for doc in value}
        missing = REQUIRED_DOC_TYPES - submitted_types
        if missing:
            raise serializers.ValidationError(
                f"Missing required documents: {', '.join(sorted(missing))}."
            )
        return value

    def validate(self, data):
        if data.get("password") != data.get("confirm_password"):
            raise serializers.ValidationError("Passwords do not match.")

        affiliation_code = data.get("affiliation_code")
        if affiliation_code and affiliation_code.strip():
            from dispatcher.models import DispatcherProfile

            dispatcher = DispatcherProfile.objects.filter(
                affiliation_code__iexact=affiliation_code.strip()
            ).first()
            if not dispatcher:
                raise serializers.ValidationError(
                    {"affiliation_code": "Invalid affiliation code."}
                )
            data["_dispatcher"] = dispatcher

        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        rider_documents = validated_data.pop("rider_documents")
        dispatcher = validated_data.pop("_dispatcher", None)
        validated_data.pop("affiliation_code", None)

        with transaction.atomic():
            user = User.objects.create_user(
                phone=validated_data["phone"],
                email=validated_data.get("email") or None,
                password=validated_data["password"],
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                contact_name=f"{validated_data['first_name']} {validated_data['last_name']}",
                usertype="Rider",
                address=validated_data["address"],
                bvn=validated_data["bvn"],
            )

            rider = Rider.objects.create(
                user=user,
                working_type="freelancer",
                is_independent_rider=True,
                is_authorized=False,
                approval_status=Rider.ApprovalStatus.PENDING,
                address=validated_data["address"],
                emergency_contact_name=validated_data["emergency_contact_name"],
                emergency_phone=validated_data["emergency_phone"],
                vehicle_model=validated_data["vehicle_model"],
                vehicle_plate_number=validated_data["vehicle_plate_number"],
                vehicle_color=validated_data["vehicle_color"],
                vehicle_photo=validated_data["vehicle_photo"],
                affiliated_to=dispatcher,
                is_affiliated=bool(dispatcher),
                affiliated_at=timezone.now() if dispatcher else None,
            )

            RiderDocument.objects.bulk_create(
                [
                    RiderDocument(
                        rider=rider, doc_type=doc["type"], file_url=doc["url"]
                    )
                    for doc in rider_documents
                ]
            )

        return {"user": user, "rider": rider}


class RiderAffiliationSerializer(serializers.Serializer):
    """
    Serializer for existing riders to affiliate with a dispatcher.
    """

    affiliation_code = serializers.CharField(required=True, max_length=100)

    def validate_affiliation_code(self, value):
        from dispatcher.models import DispatcherProfile

        if not value or not value.strip():
            raise serializers.ValidationError("Affiliation code is required.")
        dispatcher = DispatcherProfile.objects.filter(
            affiliation_code__iexact=value.strip()
        ).first()
        if not dispatcher:
            raise serializers.ValidationError(
                "Invalid affiliation code. No dispatcher found with this code."
            )
        return value.strip().upper()


class RiderAffiliationResponseSerializer(serializers.Serializer):
    """
    Serializer for returning rider affiliation status and details.
    """

    is_affiliated = serializers.BooleanField()
    affiliated_at = serializers.DateTimeField(allow_null=True)
    dispatcher = serializers.DictField(allow_null=True)


class RiderDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for a rider viewing their own KYC documents and review status.
    """

    class Meta:
        model = RiderDocument
        fields = [
            "id",
            "doc_type",
            "file_url",
            "status",
            "expires_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RiderDocumentReuploadSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)


class RiderOrderSerializer(AssignedOrderSerializer):
    """
    Serializer for rider order history and details.
    Matches the specific format requested by the user.
    """

    # id = serializers.CharField(source="order_number", read_only=True)
    status = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "pickup_address",
            "pickup_latitude",
            "pickup_longitude",
            "pickup_contact_name",
            "pickup_contact_phone",
            "pickup_notes",
            "dropoff_address",
            "dropoff_latitude",
            "dropoff_longitude",
            "dropoff_contact_name",
            "dropoff_contact_phone",
            "dropoff_notes",
            "total_amount",
            "vehicle_type",
            "payment_method",
            "merchant_name",
            "estimated_earnings",
            "distance_km",
            "eta_mins",
            "cod_amount",
            "cod_from",
            "created_at",
            "delivered_at",
            "delivery_proofs",
        ]

    def get_status(self, obj):
        status_map = {
            "Pending": "pending",
            "Assigned": "assigned",
            "PickedUp": "picked_up",
            "Started": "started",
            "Done": "delivered",
            "CustomerCanceled": "customer_canceled",
            "RiderCanceled": "rider_canceled",
            "Failed": "failed",
        }
        return status_map.get(obj.status, obj.status.lower())

    def get_payment_method(self, obj):
        # Map our internal choices to mobile expectations
        if obj.payment_method in ["cash_on_pickup", "receiver_pays"]:
            return "cod"
        return obj.payment_method.lower()

    def get_delivered_at(self, obj):
        val = super().get_delivered_at(obj)
        if val and hasattr(val, "strftime"):
            return val.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        return val


class OrderOfferListSerializer(serializers.ModelSerializer):
    """
    Serializer for unassigned order offers shown to riders.
    Matches the specific format requested for the mobile app.
    """

    order_id = serializers.CharField(source="order.id", read_only=True)
    order_ref = serializers.CharField(source="order.order_number", read_only=True)
    estimated_distance_km = serializers.DecimalField(
        source="order.distance_km", max_digits=10, decimal_places=2, read_only=True
    )
    estimated_eta_mins = serializers.IntegerField(
        source="order.duration_minutes", read_only=True
    )
    pickup_address = serializers.CharField(
        source="order.pickup_address", read_only=True
    )
    pickup_latitude = serializers.FloatField(
        source="order.pickup_latitude", read_only=True
    )
    pickup_longitude = serializers.FloatField(
        source="order.pickup_longitude", read_only=True
    )
    vehicle_type = serializers.CharField(source="order.vehicle.name", read_only=True)
    payment_method = serializers.SerializerMethodField()
    merchant_name = serializers.CharField(
        source="order.user.business_name", read_only=True
    )
    pickup_contact_name = serializers.CharField(
        source="order.sender_name", read_only=True
    )
    total_amount = serializers.DecimalField(
        source="order.total_amount", max_digits=10, decimal_places=2, read_only=True
    )
    created_at = serializers.DateTimeField(source="order.created_at", read_only=True)

    dropoff_address = serializers.SerializerMethodField()
    dropoff_latitude = serializers.SerializerMethodField()
    dropoff_longitude = serializers.SerializerMethodField()
    dropoff_contact_name = serializers.SerializerMethodField()
    cod_amount = serializers.SerializerMethodField()

    class Meta:
        model = OrderOffer
        fields = [
            "id",
            "order_id",
            "order_ref",
            "status",
            "total_amount",
            "estimated_earnings",
            "estimated_distance_km",
            "estimated_eta_mins",
            "pickup_address",
            "dropoff_address",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "vehicle_type",
            "payment_method",
            "merchant_name",
            "created_at",
            "pickup_contact_name",
            "dropoff_contact_name",
            "cod_amount",
        ]

    def _get_first_delivery(self, obj):
        if not hasattr(obj, "_first_delivery"):
            obj._first_delivery = obj.order.deliveries.first()
        return obj._first_delivery

    def get_payment_method(self, obj):
        if obj.order.payment_method in ["cash_on_pickup", "receiver_pays"]:
            return "cod"
        return obj.order.payment_method.lower()

    def get_dropoff_address(self, obj):
        d = self._get_first_delivery(obj)
        return d.dropoff_address if d else ""

    def get_dropoff_latitude(self, obj):
        d = self._get_first_delivery(obj)
        return d.dropoff_latitude if d else None

    def get_dropoff_longitude(self, obj):
        d = self._get_first_delivery(obj)
        return d.dropoff_longitude if d else None

    def get_dropoff_contact_name(self, obj):
        d = self._get_first_delivery(obj)
        return d.receiver_name if d else ""

    def get_cod_amount(self, obj):
        d = self._get_first_delivery(obj)
        return float(d.cod_amount) if d else 0.0


class RiderEarningsStatsSerializer(serializers.Serializer):
    """
    Serializer for the rider earnings summary screen.
    """

    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    trips_completed = serializers.IntegerField()
    cod_collected = serializers.DecimalField(max_digits=12, decimal_places=2)


class RiderTodayTripSerializer(serializers.ModelSerializer):
    """
    Serializer for the 'Today's Trips' list.
    Matches the specific flat format for the UI.
    """

    id = serializers.CharField(source="order_number", read_only=True)
    route = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    earned = serializers.SerializerMethodField()
    cod = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "route", "time", "distance", "earned", "cod"]

    def get_route(self, obj):
        # Format: "PickupArea -> DropoffArea"
        # Since we don't have explicit 'area' names in Order, we'll use a simplified address part or fallback
        pickup = obj.pickup_address.split(",")[0].strip()
        first_delivery = obj.deliveries.first()
        dropoff = (
            first_delivery.dropoff_address.split(",")[0].strip()
            if first_delivery
            else "Unknown"
        )
        return f"{pickup} -> {dropoff}"

    def get_time(self, obj):
        # Format: "2:15 PM"
        if obj.completed_at:
            return obj.completed_at.strftime("%-I:%M %p")
        return ""

    def get_distance(self, obj):
        # Format: "12.4km"
        val = obj.distance_km or 0
        return f"{val}km"

    def get_earned(self, obj):
        # Try to find the associated earnings
        from .models import RiderEarning

        earning = RiderEarning.objects.filter(order=obj).first()
        if earning:
            return float(earning.net_earning)
        return 0.0

    def get_cod(self, obj):
        # Total COD for the order
        total = obj.deliveries.aggregate(Sum("cod_amount"))["cod_amount__sum"] or 0
        return float(total)


class RiderWalletInfoSerializer(serializers.Serializer):
    """
    Serializer for the rider wallet info screen.
    Includes Available Balance and Pending COD.
    """

    available_balance = serializers.SerializerMethodField()
    pending_cod = serializers.SerializerMethodField()
    withdrawable_balance = serializers.SerializerMethodField()
    has_transaction_pin = serializers.BooleanField(read_only=True)

    def get_withdrawable_balance(self, obj):
        # Withdrawable Balance = Available Balance - Pending COD
        available_balance = self.get_available_balance(obj)
        pending_cod = self.get_pending_cod(obj)
        amount_can_withdraw = float(available_balance - pending_cod)
        return max(amount_can_withdraw, 0)

    def get_available_balance(self, obj):
        # Available Balance = Wallet Balance + Pending COD
        try:
            from wallet.models import Wallet

            wallet = Wallet.objects.get(user=obj.user)
            wallet_balance = wallet.balance
        except Wallet.DoesNotExist:
            wallet_balance = 0.00

        pending_cod = self.get_pending_cod(obj)
        return float(wallet_balance) + pending_cod

    def get_pending_cod(self, obj):
        # Sum of pending COD records
        total = obj.cod_records.filter(status="pending").aggregate(Sum("amount"))[
            "amount__sum"
        ]
        return float(total or 0.00)


class RiderTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for wallet transactions shown to riders.
    """

    title = serializers.CharField(source="description", read_only=True)
    time = serializers.SerializerMethodField()
    type = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Transaction
        fields = ["id", "type", "amount", "title", "time", "status"]

    def get_time(self, obj):
        # Format: "2:15 PM"
        return obj.created_at.strftime("%-I:%M %p")


class RiderLocationSerializer(serializers.Serializer):
    """
    Input serializer for the rider location update endpoint.
    """

    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    accuracy = serializers.FloatField(required=False, allow_null=True)
    heading = serializers.FloatField(required=False, allow_null=True)
    speed = serializers.FloatField(required=False, allow_null=True)


class RiderNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for rider notifications.
    """

    class Meta:
        model = RiderNotification
        fields = [
            "id",
            "title",
            "body",
            "data",
            "is_read",
            "created_at",
        ]


# ---------------------------------------------------------------------------
# Rider Document (KYC) Serializers
# ---------------------------------------------------------------------------

RIDER_DOCUMENT_ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "application/pdf",
}
RIDER_DOCUMENT_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


class RiderDocumentListSerializer(serializers.ModelSerializer):
    """
    Output serializer for the rider's document list screen.
    """

    doc_type_display = serializers.CharField(
        source="get_doc_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = RiderDocument
        fields = [
            "id",
            "doc_type",
            "doc_type_display",
            "status",
            "status_display",
            "file_url",
            "expires_at",
            "created_at",
        ]


class RiderDocumentDetailSerializer(serializers.ModelSerializer):
    """
    Output serializer for a single rider document, including rejection reason.
    """

    doc_type_display = serializers.CharField(
        source="get_doc_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = RiderDocument
        fields = [
            "id",
            "doc_type",
            "doc_type_display",
            "status",
            "status_display",
            "file_url",
            "expires_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]


class RiderDocumentCreateSerializer(serializers.Serializer):
    """
    Input serializer for uploading a new KYC document.
    """

    doc_type = serializers.ChoiceField(choices=RiderDocument.DocType.choices)
    file = serializers.FileField()
    expires_at = serializers.DateField(required=False, allow_null=True)

    def validate_file(self, file_obj):
        if file_obj.size > RIDER_DOCUMENT_MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError("File size must not exceed 10MB.")
        content_type = getattr(file_obj, "content_type", "")
        if content_type not in RIDER_DOCUMENT_ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError(
                "Unsupported file type. Only JPEG, PNG, and PDF files are allowed."
            )
        return file_obj

    def validate_expires_at(self, value):
        if value and value <= timezone.now().date():
            raise serializers.ValidationError("Expiry date must be in the future.")
        return value


class RiderDocumentCreateResponseSerializer(serializers.ModelSerializer):
    """
    Output serializer returned after a document is uploaded.
    """

    doc_type_display = serializers.CharField(
        source="get_doc_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = RiderDocument
        fields = [
            "id",
            "doc_type",
            "doc_type_display",
            "status",
            "status_display",
            "file_url",
            "expires_at",
            "created_at",
        ]


class RiderDocumentUpdateSerializer(serializers.Serializer):
    """
    Input serializer for updating an existing document: re-upload the file
    and/or change the expiry date. At least one of the two must be provided.
    """

    file = serializers.FileField(required=False)
    expires_at = serializers.DateField(required=False, allow_null=True)

    def validate_file(self, file_obj):
        if file_obj.size > RIDER_DOCUMENT_MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError("File size must not exceed 10MB.")
        content_type = getattr(file_obj, "content_type", "")
        if content_type not in RIDER_DOCUMENT_ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError(
                "Unsupported file type. Only JPEG, PNG, and PDF files are allowed."
            )
        return file_obj

    def validate_expires_at(self, value):
        if value and value <= timezone.now().date():
            raise serializers.ValidationError("Expiry date must be in the future.")
        return value

    def validate(self, data):
        if "file" not in data and "expires_at" not in data:
            raise serializers.ValidationError(
                "Provide at least a file or an expiry date to update."
            )
        return data


class RiderDocumentUpdateResponseSerializer(serializers.ModelSerializer):
    """
    Output serializer returned after a document is updated.
    """

    doc_type_display = serializers.CharField(
        source="get_doc_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = RiderDocument
        fields = [
            "id",
            "doc_type",
            "doc_type_display",
            "status",
            "status_display",
            "file_url",
            "expires_at",
            "rejection_reason",
            "updated_at",
        ]


class RiderRatingSerializer(serializers.Serializer):
    """
    Serializer for rider rating input.
    """

    rider_id = serializers.CharField(required=True)
    rating = serializers.IntegerField(min_value=1, max_value=5, required=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class BankListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing supported Nigerian banks.
    """

    class Meta:
        from wallet.models import Bank

        model = Bank
        fields = [
            "id",
            "name",
            "bank_code",
            "cbn_code",
            "ussd_short_code",
            "bank_short_name",
        ]


class VerifyAccountSerializer(serializers.Serializer):
    """
    Serializer for validating account enquiry input parameters.
    """

    account_number = serializers.CharField(required=True)
    bank_code = serializers.CharField(required=True)

    def validate(self, attrs):
        account_number = str(attrs.get("account_number", "")).strip()
        bank_code = str(attrs.get("bank_code", "")).strip()

        if not account_number or not bank_code:
            raise ServiceException(
                status_code=400, message="account_number and bank_code are required."
            )

        if not account_number.isdigit() or len(account_number) != 10:
            raise ServiceException(
                status_code=400,
                message="Account number must be a valid 10-digit NUBAN number.",
            )

        attrs["account_number"] = account_number
        attrs["bank_code"] = bank_code
        return attrs


class RiderWithdrawalSerializer(serializers.Serializer):
    """
    Serializer for rider wallet earnings withdrawal request.
    Supports optional sandbox execution for testing and simulation.
    """

    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    account_number = serializers.CharField(required=True)
    account_name = serializers.CharField(required=True)
    bank_code = serializers.CharField(required=True)
    bank_name = serializers.CharField(required=False, allow_blank=True, default="")
    narration = serializers.CharField(required=False, allow_blank=True, default="")
    is_sandbox = serializers.BooleanField(required=False, default=None)
    mode = serializers.CharField(required=False, allow_blank=True, default=None)
    pin = serializers.CharField(
        required=True,
        write_only=True,
        help_text="4-digit transaction PIN for withdrawal authorization",
    )

    def validate(self, attrs):
        from decimal import Decimal

        amount = attrs.get("amount")
        account_number = str(attrs.get("account_number", "")).strip()
        account_name = str(attrs.get("account_name", "")).strip()
        bank_code = str(attrs.get("bank_code", "")).strip()
        pin = str(attrs.get("pin", "")).strip()

        if not pin:
            raise ServiceException(
                status_code=400, message="Transaction PIN is required."
            )

        if not pin.isdigit() or len(pin) != 4:
            raise ServiceException(
                status_code=400, message="Transaction PIN must be exactly 4 digits."
            )

        if amount is None or amount <= Decimal("0.00"):
            raise ServiceException(
                status_code=400, message="Withdrawal amount must be greater than zero."
            )

        if amount < Decimal("100.00"):
            raise ServiceException(
                status_code=400, message="Minimum withdrawal amount is ₦100.00."
            )

        if not account_number or not account_number.isdigit() or len(account_number) != 10:
            raise ServiceException(
                status_code=400,
                message="A valid 10-digit account number is required.",
            )

        if not account_name:
            raise ServiceException(
                status_code=400, message="Account name is required."
            )

        if not bank_code:
            raise ServiceException(
                status_code=400, message="Bank code is required."
            )

        attrs["pin"] = pin
        attrs["account_number"] = account_number
        attrs["account_name"] = account_name
        attrs["bank_code"] = bank_code

        # Determine sandbox mode: explicit is_sandbox, explicit mode, or system settings default
        is_sandbox_arg = attrs.get("is_sandbox")
        mode_arg = (attrs.get("mode") or "").strip().upper()

        if is_sandbox_arg is True or mode_arg == "SANDBOX":
            attrs["mode"] = "SANDBOX"
            attrs["is_sandbox"] = True
        elif is_sandbox_arg is False or mode_arg == "LIVE":
            attrs["mode"] = "LIVE"
            attrs["is_sandbox"] = False
        else:
            default_mode = getattr(settings, "WIHDRAWAL_MODE", getattr(settings, "COREBANKING_MODE", "SANDBOX")).upper()
            attrs["mode"] = default_mode
            attrs["is_sandbox"] = (default_mode == "SANDBOX")

        return attrs


class RiderSetTransactionPinSerializer(serializers.Serializer):
    """
    Serializer for setting or changing a rider's 4-digit transaction PIN.
    """

    old_pin = serializers.CharField(
        required=False,
        write_only=True,
        allow_blank=True,
        default="",
        help_text="Current transaction PIN (required if PIN is already configured)",
    )
    password = serializers.CharField(
        required=False,
        write_only=True,
        allow_blank=True,
        default="",
        help_text="Account login password (fallback if current PIN is forgotten)",
    )
    pin = serializers.CharField(
        required=True,
        write_only=True,
        help_text="New 4-digit transaction PIN",
    )
    confirm_pin = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Confirm new 4-digit transaction PIN",
    )

    def validate(self, attrs):
        pin = str(attrs.get("pin", "")).strip()
        confirm_pin = str(attrs.get("confirm_pin", "")).strip()
        old_pin = str(attrs.get("old_pin", "")).strip()

        if not pin or not pin.isdigit() or len(pin) != 4:
            raise ServiceException(
                status_code=400, message="Transaction PIN must be exactly 4 digits."
            )

        if pin != confirm_pin:
            raise ServiceException(
                status_code=400, message="PIN and confirmation PIN do not match."
            )

        if old_pin and not old_pin.isdigit():
            raise ServiceException(
                status_code=400, message="Current transaction PIN must be numeric."
            )

        attrs["pin"] = pin
        attrs["confirm_pin"] = confirm_pin
        attrs["old_pin"] = old_pin
        return attrs


class RiderVerifyTransactionPinSerializer(serializers.Serializer):
    """
    Serializer for validating rider transaction PIN input.
    """

    pin = serializers.CharField(
        required=True,
        write_only=True,
        help_text="4-digit transaction PIN to verify",
    )

    def validate(self, attrs):
        pin = str(attrs.get("pin", "")).strip()
        if not pin or not pin.isdigit() or len(pin) != 4:
            raise ServiceException(
                status_code=400, message="Transaction PIN must be exactly 4 digits."
            )
        attrs["pin"] = pin
        return attrs


class RiderFaceMatchRequestSerializer(serializers.Serializer):
    """
    Serializer for independent rider face match request.
    Expects the S3 storage bucket URL of the selfie snapshot.
    """

    image_url = serializers.URLField(
        required=True,
        max_length=500,
        help_text="URL of the uploaded selfie snapshot image in the storage bucket",
    )

    def validate_image_url(self, value):
        url = str(value).strip()
        if not url:
            raise ServiceException(
                status_code=400, message="image_url cannot be empty."
            )
        return url


class RiderFaceMatchLogSerializer(serializers.ModelSerializer):
    """
    Serializer for independent rider face verification audit logs.
    """

    rider_id = serializers.CharField(source="rider.rider_id", read_only=True)
    rider_name = serializers.SerializerMethodField()

    class Meta:
        model = RiderFaceMatchLog
        fields = [
            "id",
            "rider_id",
            "rider_name",
            "trigger_type",
            "status",
            "similarity",
            "is_match",
            "selfie_url",
            "reference_photo_url",
            "error_message",
            "created_at",
            "updated_at",
        ]

    def get_rider_name(self, obj):
        if obj.rider and obj.rider.user:
            return (
                obj.rider.user.contact_name
                or f"{obj.rider.user.first_name} {obj.rider.user.last_name}".strip()
            )
        return ""


