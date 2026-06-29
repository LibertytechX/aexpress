"""Serializers for the Operations Dashboard app."""

from rest_framework import serializers

from orders.models import Order

from .models import Alert, AlertRule


class AlertSerializer(serializers.ModelSerializer):
    """Read serializer for Alert, with a few denormalized subject labels."""

    rider_code = serializers.SerializerMethodField()
    order_number = serializers.SerializerMethodField()
    vehicle_plate = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            "id",
            "alert_type",
            "severity",
            "entity_type",
            "title",
            "description",
            "value",
            "context",
            "dedupe_key",
            "status",
            "resolution_note",
            "resolved_at",
            "first_seen_at",
            "last_seen_at",
            "created_at",
            "updated_at",
            "rider",
            "order",
            "merchant",
            "vehicle",
            "zone",
            "rider_code",
            "order_number",
            "vehicle_plate",
        ]
        read_only_fields = fields

    def get_rider_code(self, obj):
        return obj.rider.rider_id if obj.rider_id else None

    def get_order_number(self, obj):
        return obj.order.order_number if obj.order_id else None

    def get_vehicle_plate(self, obj):
        return obj.vehicle.plate_number if obj.vehicle_id else None


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full order detail for payment/order drill-down lists."""

    merchant = serializers.SerializerMethodField()
    rider_code = serializers.SerializerMethodField()
    rider_name = serializers.SerializerMethodField()
    vehicle = serializers.CharField(source="vehicle.name", default=None)
    deliveries = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "total_amount",
            "payment_method",
            "payment_status",
            "collect_on_delivery",
            "cod_amount",
            "distance_km",
            "duration_minutes",
            "pickup_address",
            "sender_name",
            "sender_phone",
            "created_at",
            "assigned_at",
            "picked_up_at",
            "arrived_at",
            "completed_at",
            "canceled_at",
            "merchant",
            "rider_code",
            "rider_name",
            "vehicle",
            "deliveries",
        ]

    def get_merchant(self, obj):
        return obj.user.business_name if obj.user_id else None

    def get_rider_code(self, obj):
        return obj.rider.rider_id if obj.rider_id else None

    def get_rider_name(self, obj):
        if not obj.rider_id:
            return None
        return obj.rider.user.contact_name or obj.rider.user.get_full_name()

    def get_deliveries(self, obj):
        return [
            {
                "receiver_name": d.receiver_name,
                "receiver_phone": d.receiver_phone,
                "dropoff_address": d.dropoff_address,
                "status": d.status,
                "cod_amount": str(d.cod_amount),
            }
            for d in obj.deliveries.all()
        ]


class CodOrderSerializer(OrderDetailSerializer):
    """Order detail + the COD settlement records (for COD drill-down)."""

    cod_records = serializers.SerializerMethodField()

    class Meta(OrderDetailSerializer.Meta):
        fields = OrderDetailSerializer.Meta.fields + ["cod_records"]

    def get_cod_records(self, obj):
        return [
            {
                "status": c.status,
                "amount": str(c.amount),
                "remitted_at": c.remitted_at.isoformat() if c.remitted_at else None,
                "verified_at": c.verified_at.isoformat() if c.verified_at else None,
            }
            for c in obj.cod_records.all()
        ]


class AlertRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRule
        fields = [
            "id",
            "alert_type",
            "is_enabled",
            "default_severity",
            "warn_threshold",
            "critical_threshold",
            "window_minutes",
            "params",
            "description",
            "updated_at",
        ]
        read_only_fields = ["id", "alert_type", "updated_at"]
