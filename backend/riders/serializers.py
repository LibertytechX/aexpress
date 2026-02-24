from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db.models import Sum
from dispatcher.models import Rider
from authentication.models import User
from wallet.models import Wallet
from .models import RiderAuth, RiderDevice, RiderCodRecord, OrderOffer, AreaDemand
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

    class Meta:
        model = Rider
        fields = [
            "id",
            "rider_id",
            "status",
            "firstName",
            "lastName",
            "phone",
            "email",
            "vehicle_model",
            "vehicle_plate_number",
            "rating",
            "total_deliveries",
            "wallet_balance",
            "pending_cod",
            "acceptance_rate",
            "on_time_rate",
            "documents_status",
        ]

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

    status = serializers.ChoiceField(choices=["on_duty", "off_duty"])
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
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
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid phone number or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

        # Authenticate user
        user = authenticate(username=phone, password=password)
        if not user:
            raise serializers.ValidationError("Invalid phone number or password.")

        # Ensure user has a rider profile
        try:
            rider = user.rider_profile
        except Rider.DoesNotExist:
            raise serializers.ValidationError(
                "No rider profile associated with this account."
            )

        data["rider"] = rider
        return data


class RiderOrderSerializer(AssignedOrderSerializer):
    """
    Serializer for rider order history and details.
    Matches the specific format requested by the user.
    """

    id = serializers.CharField(source="order_number", read_only=True)
    status = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
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
