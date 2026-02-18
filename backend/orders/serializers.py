from rest_framework import serializers
from .models import Order, Delivery, Vehicle
from authentication.serializers import UserSerializer


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for Vehicle model."""

    class Meta:
        model = Vehicle
        fields = ['id', 'name', 'max_weight_kg', 'base_price', 'base_fare', 'rate_per_km', 'rate_per_minute', 'description', 'is_active']


class DeliverySerializer(serializers.ModelSerializer):
    """Serializer for Delivery model."""

    class Meta:
        model = Delivery
        fields = [
            'id', 'dropoff_address', 'receiver_name', 'receiver_phone',
            'package_type', 'notes', 'status', 'sequence',
            'created_at', 'delivered_at'
        ]
        read_only_fields = ['id', 'created_at', 'delivered_at']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model - for listing and detail views."""

    deliveries = DeliverySerializer(many=True, read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    vehicle_price = serializers.DecimalField(source='vehicle.base_price', max_digits=10, decimal_places=2, read_only=True)
    vehicle_base_fare = serializers.DecimalField(source='vehicle.base_fare', max_digits=10, decimal_places=2, read_only=True)
    vehicle_rate_per_km = serializers.DecimalField(source='vehicle.rate_per_km', max_digits=10, decimal_places=2, read_only=True)
    vehicle_rate_per_minute = serializers.DecimalField(source='vehicle.rate_per_minute', max_digits=10, decimal_places=2, read_only=True)
    user_business_name = serializers.CharField(source='user.business_name', read_only=True)
    delivery_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user_business_name', 'mode', 'vehicle_name', 'vehicle_price',
            'vehicle_base_fare', 'vehicle_rate_per_km', 'vehicle_rate_per_minute',
            'pickup_address', 'sender_name', 'sender_phone',
            'payment_method', 'total_amount', 'distance_km', 'duration_minutes', 'status',
            'created_at', 'updated_at', 'scheduled_pickup_time',
            'notes', 'deliveries', 'delivery_count'
        ]
        read_only_fields = ['id', 'order_number', 'created_at', 'updated_at']

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
        choices=['wallet', 'cash_on_pickup', 'receiver_pays'],
        default='wallet'
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    package_type = serializers.ChoiceField(
        choices=['Box', 'Envelope', 'Fragile', 'Food', 'Document', 'Other'],
        default='Box'
    )
    scheduled_pickup_time = serializers.DateTimeField(required=False, allow_null=True)

    # Route information for pricing
    distance_km = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)
    duration_minutes = serializers.IntegerField(required=True)

    def validate_vehicle(self, value):
        """Validate that the vehicle exists."""
        try:
            Vehicle.objects.get(name=value, is_active=True)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError(f"Vehicle '{value}' not found or inactive.")
        return value


class MultiDropDeliverySerializer(serializers.Serializer):
    """Serializer for individual delivery in multi-drop."""

    dropoff_address = serializers.CharField(required=True)
    receiver_name = serializers.CharField(required=True, max_length=255)
    receiver_phone = serializers.CharField(required=True, max_length=20)
    package_type = serializers.ChoiceField(
        choices=['Box', 'Envelope', 'Fragile', 'Food', 'Document', 'Other'],
        default='Box'
    )
    notes = serializers.CharField(required=False, allow_blank=True)


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
        choices=['wallet', 'cash_on_pickup', 'receiver_pays'],
        default='wallet'
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    scheduled_pickup_time = serializers.DateTimeField(required=False, allow_null=True)

    # Route information for pricing
    distance_km = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)
    duration_minutes = serializers.IntegerField(required=True)

    def validate_vehicle(self, value):
        """Validate that the vehicle exists."""
        try:
            Vehicle.objects.get(name=value, is_active=True)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError(f"Vehicle '{value}' not found or inactive.")
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
        choices=['wallet', 'cash_on_pickup', 'receiver_pays'],
        default='wallet'
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    scheduled_pickup_time = serializers.DateTimeField(required=False, allow_null=True)

    # Route information for pricing
    distance_km = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)
    duration_minutes = serializers.IntegerField(required=True)

    def validate_vehicle(self, value):
        """Validate that the vehicle exists."""
        try:
            Vehicle.objects.get(name=value, is_active=True)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError(f"Vehicle '{value}' not found or inactive.")
        return value

    def validate_deliveries(self, value):
        """Validate that there's at least one delivery."""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one delivery is required.")
        return value

