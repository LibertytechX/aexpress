from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db.models import Sum
from dispatcher.models import Rider
from authentication.models import User
from wallet.models import Wallet, Transaction
from .models import (
    RiderAuth,
    RiderDevice,
    RiderCodRecord,
    OrderOffer,
    AreaDemand,
    RiderEarning,
    RiderNotification,
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
        data["user"] = user
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

    def get_withdrawable_balance(self, obj):
        # Withdrawable Balance = Available Balance - Pending COD
        available_balance = self.get_available_balance(obj)
        pending_cod = self.get_pending_cod(obj)
        amount_can_withdraw = float(available_balance - pending_cod)
        return max(amount_can_withdraw, 0)

    def get_available_balance(self, obj):
        # Available Balance = Wallet Balance + Pending COD
        try:
            wallet_balance = obj.user.wallet.balance
        except (AttributeError, Wallet.DoesNotExist):
            wallet_balance = 0.00

        # Sum of pending COD records
        # pending_cod = (
        #     obj.cod_records.filter(status="pending").aggregate(Sum("amount"))[
        #         "amount__sum"
        #     ]
        #     or 0.00
        # )
        return float(wallet_balance)

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
