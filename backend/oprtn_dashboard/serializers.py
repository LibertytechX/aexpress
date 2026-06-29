"""Serializers for the Operations Dashboard app."""

from rest_framework import serializers

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
