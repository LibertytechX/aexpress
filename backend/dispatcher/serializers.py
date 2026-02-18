from rest_framework import serializers
from .models import Rider, DispatcherProfile
from authentication.serializers import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class DispatcherProfileSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source="user", read_only=True)

    class Meta:
        model = DispatcherProfile
        fields = ["id", "user_details", "created_at"]


class DispatcherSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["phone", "email", "password", "contact_name", "business_name"]

    def create(self, validated_data):
        validated_data["usertype"] = "Dispatcher"
        user = User.objects.create_user(**validated_data)
        return user


class RiderSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.contact_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)

    # Vehicle fields from Rider model
    vehicle = serializers.SerializerMethodField()

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


class OrderSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="order_number", read_only=True)
    merchant = serializers.CharField(source="user.business_name", read_only=True)
    rider = serializers.SerializerMethodField()
    riderId = serializers.SerializerMethodField()
    amount = serializers.DecimalField(
        source="total_amount", max_digits=10, decimal_places=2, read_only=True
    )
    created = serializers.DateTimeField(
        source="created_at", format="%Y-%m-%d %H:%M", read_only=True
    )

    # Computed fields
    pickup = serializers.CharField(source="pickup_address", read_only=True)
    dropoff = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    customerPhone = serializers.SerializerMethodField()
    vehicle = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    pkg = serializers.SerializerMethodField()
    codFee = serializers.SerializerMethodField()

    # Extra fields for backward compatibility or extra detail
    items = serializers.SerializerMethodField()
    cod = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    timeline = serializers.SerializerMethodField()

    class Meta:
        from orders.models import Order

        model = Order
        fields = [
            "id",
            "pickup",
            "dropoff",
            "merchant",
            "riderId",
            "rider",
            "status",
            "amount",
            "distance",
            "time",
            "created",
            "cod",
            "codFee",
            "payment",
            "items",
            "pkg",
            "notes",
            "timeline",
            "customer",
            "customerPhone",
            "vehicle",
        ]

    def get_rider(self, obj):
        if obj.rider and obj.rider.user:
            return obj.rider.user.contact_name
        return None

    def get_riderId(self, obj):
        if obj.rider:
            return obj.rider.rider_id
        return None

    def get_dropoff(self, obj):
        # Return first delivery dropoff or empty
        first = obj.deliveries.first()
        return first.dropoff_address if first else ""

    def get_customer(self, obj):
        first = obj.deliveries.first()
        return first.receiver_name if first else "Unknown"

    def get_customerPhone(self, obj):
        first = obj.deliveries.first()
        return first.receiver_phone if first else ""

    def get_vehicle(self, obj):
        return obj.vehicle.name if obj.vehicle else "Bike"

    def get_pkg(self, obj):
        first = obj.deliveries.first()
        return first.package_type if first else "Box"

    def get_codFee(self, obj):
        return 0

    def get_status(self, obj):
        mapping = {
            "Pending": "Pending",
            "Assigned": "Assigned",
            "Started": "In Transit",  # Or Picked Up
            "Done": "Delivered",
            "CustomerCanceled": "Cancelled",
            "RiderCanceled": "Cancelled",
            "Failed": "Failed",
        }
        return mapping.get(obj.status, "Pending")

    def get_items(self, obj):
        return [d.package_type for d in obj.deliveries.all()]

    def get_cod(self, obj):
        return 0  # Mock for now

    def get_payment(self, obj):
        method_map = {
            "wallet": "Wallet",
            "cash_on_pickup": "Cash on Pickup",
            "receiver_pays": "Receiver Pays",
        }
        return method_map.get(obj.payment_method, "Wallet")

    def get_distance(self, obj):
        return "5.2 km"  # Mock

    def get_time(self, obj):
        return "25 mins"  # Mock

    def get_timeline(self, obj):
        return [{"time": obj.created_at.strftime("%H:%M"), "event": "Order Placed"}]
