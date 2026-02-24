from django.db import models
from rest_framework import serializers
from .models import Order, Delivery, Vehicle
from authentication.serializers import UserSerializer


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for Vehicle model."""

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "name",
            "max_weight_kg",
            "base_price",
            "base_fare",
            "rate_per_km",
            "rate_per_minute",
            "min_distance_km",
            "min_fee",
            "description",
            "is_active",
        ]
        read_only_fields = ["id", "name"]


class DeliverySerializer(serializers.ModelSerializer):
    """Serializer for Delivery model."""

    class Meta:
        model = Delivery
        fields = [
            "id",
            "dropoff_address",
            "receiver_name",
            "receiver_phone",
            "package_type",
            "notes",
            "cod_amount",
            "status",
            "sequence",
            "created_at",
            "delivered_at",
        ]
        read_only_fields = ["id", "created_at", "delivered_at"]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model - for listing and detail views."""

    deliveries = DeliverySerializer(many=True, read_only=True)
    vehicle_name = serializers.CharField(source="vehicle.name", read_only=True)
    vehicle_price = serializers.DecimalField(
        source="vehicle.base_price", max_digits=10, decimal_places=2, read_only=True
    )
    vehicle_base_fare = serializers.DecimalField(
        source="vehicle.base_fare", max_digits=10, decimal_places=2, read_only=True
    )
    vehicle_rate_per_km = serializers.DecimalField(
        source="vehicle.rate_per_km", max_digits=10, decimal_places=2, read_only=True
    )
    vehicle_rate_per_minute = serializers.DecimalField(
        source="vehicle.rate_per_minute",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    user_business_name = serializers.CharField(
        source="user.business_name", read_only=True
    )
    delivery_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user_business_name",
            "mode",
            "vehicle_name",
            "vehicle_price",
            "vehicle_base_fare",
            "vehicle_rate_per_km",
            "vehicle_rate_per_minute",
            "pickup_address",
            "sender_name",
            "sender_phone",
            "payment_method",
            "total_amount",
            "distance_km",
            "duration_minutes",
            "status",
            "created_at",
            "updated_at",
            "scheduled_pickup_time",
            "notes",
            "deliveries",
            "delivery_count",
        ]
        read_only_fields = ["id", "order_number", "created_at", "updated_at"]

    def get_delivery_count(self, obj):
        """Get the number of deliveries for this order."""
        return obj.deliveries.count()


class QuickSendSerializer(serializers.Serializer):
    """Serializer for Quick Send order creation."""

    # Pickup details
    pickup_address = serializers.CharField(required=True)
    sender_name = serializers.CharField(required=True, max_length=255)
    sender_phone = serializers.CharField(required=True, max_length=20)

    # Dropoff details
    dropoff_address = serializers.CharField(required=True)
    receiver_name = serializers.CharField(required=True, max_length=255)
    receiver_phone = serializers.CharField(required=True, max_length=20)

    # Order details
    vehicle = serializers.CharField(required=True)
    payment_method = serializers.ChoiceField(
        choices=["wallet", "cash_on_pickup", "receiver_pays"], default="wallet"
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    package_type = serializers.ChoiceField(
        choices=["Box", "Envelope", "Fragile", "Food", "Document", "Other"],
        default="Box",
    )
    scheduled_pickup_time = serializers.DateTimeField(required=False, allow_null=True)

    # Route information for pricing
    distance_km = serializers.DecimalField(
        required=True, max_digits=10, decimal_places=2
    )
    duration_minutes = serializers.IntegerField(required=True)

    def validate_vehicle(self, value):
        """Validate that the vehicle exists."""
        try:
            Vehicle.objects.get(name=value, is_active=True)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError(
                f"Vehicle '{value}' not found or inactive."
            )
        return value


class MultiDropDeliverySerializer(serializers.Serializer):
    """Serializer for individual delivery in multi-drop."""

    dropoff_address = serializers.CharField(required=True)
    receiver_name = serializers.CharField(required=True, max_length=255)
    receiver_phone = serializers.CharField(required=True, max_length=20)
    package_type = serializers.ChoiceField(
        choices=["Box", "Envelope", "Fragile", "Food", "Document", "Other"],
        default="Box",
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    cod_amount = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2, default=0
    )


class MultiDropSerializer(serializers.Serializer):
    """Serializer for Multi-Drop order creation."""

    # Pickup details
    pickup_address = serializers.CharField(required=True)
    sender_name = serializers.CharField(required=True, max_length=255)
    sender_phone = serializers.CharField(required=True, max_length=20)

    # Multiple deliveries
    deliveries = MultiDropDeliverySerializer(many=True, required=True)

    # Order details
    vehicle = serializers.CharField(required=True)
    payment_method = serializers.ChoiceField(
        choices=["wallet", "cash_on_pickup", "receiver_pays"], default="wallet"
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    scheduled_pickup_time = serializers.DateTimeField(required=False, allow_null=True)

    # Route information for pricing
    distance_km = serializers.DecimalField(
        required=True, max_digits=10, decimal_places=2
    )
    duration_minutes = serializers.IntegerField(required=True)

    def validate_vehicle(self, value):
        """Validate that the vehicle exists."""
        try:
            Vehicle.objects.get(name=value, is_active=True)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError(
                f"Vehicle '{value}' not found or inactive."
            )
        return value

    def validate_deliveries(self, value):
        """Validate that there's at least one delivery."""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one delivery is required.")
        return value


class BulkImportSerializer(serializers.Serializer):
    """Serializer for Bulk Import order creation."""

    # Pickup details
    pickup_address = serializers.CharField(required=True)
    sender_name = serializers.CharField(required=True, max_length=255)
    sender_phone = serializers.CharField(required=True, max_length=20)

    # Bulk deliveries (same as multi-drop)
    deliveries = MultiDropDeliverySerializer(many=True, required=True)

    # Order details
    vehicle = serializers.CharField(required=True)
    payment_method = serializers.ChoiceField(
        choices=["wallet", "cash_on_pickup", "receiver_pays"], default="wallet"
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    scheduled_pickup_time = serializers.DateTimeField(required=False, allow_null=True)

    # Route information for pricing
    distance_km = serializers.DecimalField(
        required=True, max_digits=10, decimal_places=2
    )
    duration_minutes = serializers.IntegerField(required=True)

    def validate_vehicle(self, value):
        """Validate that the vehicle exists."""
        try:
            Vehicle.objects.get(name=value, is_active=True)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError(
                f"Vehicle '{value}' not found or inactive."
            )
        return value

    def validate_deliveries(self, value):
        """Validate that there's at least one delivery."""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one delivery is required.")
        return value


class AssignedOrderSerializer(serializers.ModelSerializer):
    """Serializer for orders assigned to a rider, flattened for mobile app consumption."""

    pickup_latitude = serializers.FloatField(read_only=True)
    pickup_longitude = serializers.FloatField(read_only=True)
    pickup_contact_name = serializers.CharField(source="sender_name", read_only=True)
    pickup_contact_phone = serializers.CharField(source="sender_phone", read_only=True)
    pickup_notes = serializers.CharField(source="notes", read_only=True)

    dropoff_address = serializers.SerializerMethodField()
    dropoff_latitude = serializers.SerializerMethodField()
    dropoff_longitude = serializers.SerializerMethodField()
    dropoff_contact_name = serializers.SerializerMethodField()
    dropoff_contact_phone = serializers.SerializerMethodField()
    dropoff_notes = serializers.SerializerMethodField()

    vehicle_type = serializers.CharField(source="vehicle.name", read_only=True)
    merchant_name = serializers.CharField(source="user.business_name", read_only=True)

    estimated_earnings = serializers.SerializerMethodField()
    eta_mins = serializers.IntegerField(source="duration_minutes", read_only=True)
    cod_amount = serializers.SerializerMethodField()
    cod_from = serializers.SerializerMethodField()

    delivered_at = serializers.SerializerMethodField()
    delivery_proofs = serializers.SerializerMethodField()
    package_type = serializers.SerializerMethodField()

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
            "package_type",
        ]

    def _get_first_delivery(self, obj):
        # Cache the first delivery on the object to avoid multiple queries
        if not hasattr(obj, "_first_delivery"):
            obj._first_delivery = obj.deliveries.first()
        return obj._first_delivery

    def get_package_type(self, obj):
        delivery = self._get_first_delivery(obj)
        return delivery.package_type if delivery else ""

    def get_dropoff_address(self, obj):
        delivery = self._get_first_delivery(obj)
        return delivery.dropoff_address if delivery else ""

    def get_dropoff_latitude(self, obj):
        delivery = self._get_first_delivery(obj)
        return delivery.dropoff_latitude if delivery else None

    def get_dropoff_longitude(self, obj):
        delivery = self._get_first_delivery(obj)
        return delivery.dropoff_longitude if delivery else None

    def get_dropoff_contact_name(self, obj):
        delivery = self._get_first_delivery(obj)
        return delivery.receiver_name if delivery else ""

    def get_dropoff_contact_phone(self, obj):
        delivery = self._get_first_delivery(obj)
        return delivery.receiver_phone if delivery else ""

    def get_dropoff_notes(self, obj):
        delivery = self._get_first_delivery(obj)
        return delivery.notes if delivery else ""

    def get_estimated_earnings(self, obj):
        offer = getattr(obj, "rider_offers", None)
        if offer and offer.exists():
            # Get the accepted offer, or the latest offer if none accepted
            acc = offer.filter(status="accepted").first()
            if acc:
                return float(acc.estimated_earnings)
            return float(offer.first().estimated_earnings)
        # Fallback if no specific offer earnings found
        return 0.0

    def get_cod_amount(self, obj):
        delivery = self._get_first_delivery(obj)
        if delivery and delivery.cod_amount:
            return float(delivery.cod_amount)
        return 0.0

    def get_cod_from(self, obj):
        delivery = self._get_first_delivery(obj)
        if delivery and delivery.cod_from:
            return delivery.cod_from
        return ""

    def get_delivered_at(self, obj):
        delivery = self._get_first_delivery(obj)
        return delivery.delivered_at if delivery else None

    def get_delivery_proofs(self, obj):
        # We don't have a DeliveryProof model yet, returning empty list as fallback.
        return []


class StopSerializer(serializers.ModelSerializer):
    """Serializer for individual deliveries as 'stops' in a route."""

    address = serializers.CharField(source="dropoff_address", read_only=True)
    contact_name = serializers.CharField(source="receiver_name", read_only=True)
    contact_phone = serializers.CharField(source="receiver_phone", read_only=True)

    class Meta:
        model = Delivery
        fields = [
            "id",
            "sequence",
            "status",
            "address",
            "contact_name",
            "contact_phone",
            "cod_amount",
            "notes",
        ]


class AssignedRouteSerializer(serializers.ModelSerializer):
    """Serializer for assigned orders formatted as 'routes' for mobile app."""

    ref = serializers.CharField(source="order_number", read_only=True)
    vehicle_type = serializers.CharField(source="vehicle.name", read_only=True)
    pickup_contact = serializers.CharField(source="sender_name", read_only=True)
    total_stops = serializers.SerializerMethodField()
    total_distance_km = serializers.FloatField(source="distance_km", read_only=True)
    total_estimated_time_mins = serializers.IntegerField(
        source="duration_minutes", read_only=True
    )
    total_earnings = serializers.SerializerMethodField()
    total_cod = serializers.SerializerMethodField()
    completed_stops = serializers.SerializerMethodField()
    stops = StopSerializer(many=True, source="deliveries", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "ref",
            "status",
            "vehicle_type",
            "pickup_address",
            "pickup_contact",
            "total_stops",
            "total_distance_km",
            "total_estimated_time_mins",
            "total_earnings",
            "total_cod",
            "completed_stops",
            "stops",
        ]

    def get_total_stops(self, obj):
        return obj.deliveries.count()

    def get_total_earnings(self, obj):
        offer = getattr(obj, "rider_offers", None)
        if offer and offer.exists():
            acc = offer.filter(status="accepted").first()
            if acc:
                return float(acc.estimated_earnings)
            return float(offer.first().estimated_earnings)
        return 0.0

    def get_total_cod(self, obj):
        total = obj.deliveries.aggregate(models.Sum("cod_amount"))["cod_amount__sum"]
        return float(total) if total else 0.0

    def get_completed_stops(self, obj):
        return obj.deliveries.filter(status="Delivered").count()


class OrderCancelSerializer(serializers.Serializer):
    """Serializer for order cancellation."""

    reason = serializers.CharField(required=True, max_length=500)
