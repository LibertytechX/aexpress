from django.contrib.auth import get_user_model
from rest_framework import serializers

from dispatcher.models import RelayNode, Rider, Vertical, VerticalLead, Zone, ZoneCaptain, ZoneTarget


User = get_user_model()


class AdminZoneSerializer(serializers.ModelSerializer):
    vertical_name = serializers.CharField(source="vertical.name", read_only=True)
    zone_lead_name = serializers.CharField(source="zone_lead.user.contact_name", read_only=True)

    class Meta:
        model = Zone
        fields = [
            "id",
            "name",
            "description",
            "vertical",
            "vertical_name",
            "zone_lead",
            "zone_lead_name",
            "center_lat",
            "center_lng",
            "radius_km",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminHubSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source="zone.name", read_only=True)

    class Meta:
        model = RelayNode
        fields = [
            "id",
            "name",
            "address",
            "latitude",
            "longitude",
            "zone",
            "zone_name",
            "catchment_radius_km",
            "hub_captain_name",
            "hub_captain_phone",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminZoneTargetSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source="zone.name", read_only=True)

    class Meta:
        model = ZoneTarget
        fields = [
            "id",
            "zone",
            "zone_name",
            "month",
            "target_orders",
            "target_revenue",
        ]
        read_only_fields = ["id"]

    def validate_month(self, value):
        return value.replace(day=1)


class VerticalLeadAssignmentSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    vertical = serializers.PrimaryKeyRelatedField(queryset=Vertical.objects.all())
    is_active = serializers.BooleanField(default=True)

    def save(self, **kwargs):
        user = self.validated_data["user"]
        vertical = self.validated_data["vertical"]
        is_active = self.validated_data["is_active"]

        VerticalLead.objects.filter(vertical=vertical).exclude(user=user).delete()
        VerticalLead.objects.filter(user=user).exclude(vertical=vertical).delete()
        lead, _ = VerticalLead.objects.update_or_create(
            user=user,
            defaults={"vertical": vertical, "is_active": is_active},
        )
        return lead


class ZoneCaptainAssignmentSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    zone = serializers.PrimaryKeyRelatedField(queryset=Zone.objects.all())
    is_active = serializers.BooleanField(default=True)

    def save(self, **kwargs):
        user = self.validated_data["user"]
        zone = self.validated_data["zone"]
        is_active = self.validated_data["is_active"]

        ZoneCaptain.objects.filter(zone=zone).exclude(user=user).delete()
        ZoneCaptain.objects.filter(user=user).exclude(zone=zone).delete()
        captain, _ = ZoneCaptain.objects.update_or_create(
            user=user,
            defaults={"zone": zone, "is_active": is_active},
        )
        return captain


class RiderHubAssignmentSerializer(serializers.Serializer):
    hub = serializers.PrimaryKeyRelatedField(
        queryset=RelayNode.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )

    def save(self, **kwargs):
        rider = self.context["rider"]
        rider.hub = self.validated_data.get("hub")
        rider.save(update_fields=["hub", "updated_at"])
        return rider


class VerticalLeadSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.contact_name", read_only=True)
    vertical_name = serializers.CharField(source="vertical.name", read_only=True)

    class Meta:
        model = VerticalLead
        fields = ["id", "user", "user_name", "vertical", "vertical_name", "is_active", "created_at"]


class ZoneCaptainSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.contact_name", read_only=True)
    zone_name = serializers.CharField(source="zone.name", read_only=True)

    class Meta:
        model = ZoneCaptain
        fields = ["id", "user", "user_name", "zone", "zone_name", "is_active", "created_at"]


class RiderHubSerializer(serializers.ModelSerializer):
    rider_name = serializers.CharField(source="user.contact_name", read_only=True)
    hub_name = serializers.CharField(source="hub.name", read_only=True)
    zone_id = serializers.SerializerMethodField()
    zone_name = serializers.SerializerMethodField()

    class Meta:
        model = Rider
        fields = ["id", "rider_id", "rider_name", "hub", "hub_name", "zone_id", "zone_name"]

    def get_zone_id(self, obj):
        if obj.hub and obj.hub.zone_id:
            return str(obj.hub.zone_id)
        return None

    def get_zone_name(self, obj):
        if obj.hub and obj.hub.zone:
            return obj.hub.zone.name
        return None
