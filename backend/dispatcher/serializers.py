from rest_framework import serializers
from .models import Rider
from authentication.serializers import UserSerializer
from orders.models import Vehicle


class RiderSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.contact_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)

    # Vehicle fields from Rider model
    vehicle = serializers.SerializerMethodField()
    vehicle_details = serializers.SerializerMethodField()

    # Mock/Computed fields to match frontend interface
    todayOrders = serializers.IntegerField(default=0, read_only=True)
    todayEarnings = serializers.IntegerField(default=0, read_only=True)
    completionRate = serializers.IntegerField(default=98, read_only=True)
    avgTime = serializers.CharField(default="25 mins", read_only=True)
    joined = serializers.DateTimeField(
        source="created_at", format="%Y-%m-%d", read_only=True
    )

    class Meta:
        model = Rider
        fields = [
            "id",
            "rider_id",
            "name",
            "phone",
            "vehicle",
            "vehicle_details",
            "plate_number",
            "model",
            "color",
            "status",
            "rating",
            "total_deliveries",
            "current_order",
            "todayOrders",
            "todayEarnings",
            "completionRate",
            "avgTime",
            "joined",
        ]

    def get_vehicle(self, obj):
        if obj.vehicle_type:
            return obj.vehicle_type.name
        return "None"

    def get_vehicle_details(self, obj):
        if obj.vehicle_type:
            return {
                "type": obj.vehicle_type.name,
                "plate_number": obj.plate_number,
                "model": obj.model,
                "color": obj.color,
            }
        return None
