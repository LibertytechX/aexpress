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


class OrderCreateSerializer(serializers.ModelSerializer):
    # Input fields from Frontend
    pickup = serializers.CharField(write_only=True)
    dropoff = serializers.CharField(write_only=True)
    senderName = serializers.CharField(write_only=True)
    senderPhone = serializers.CharField(write_only=True)
    receiverName = serializers.CharField(write_only=True)
    receiverPhone = serializers.CharField(write_only=True)
    vehicle = serializers.CharField(write_only=True)  # "Bike", "Car", etc.
    packageType = serializers.CharField(write_only=True)
    price = serializers.DecimalField(
        write_only=True, required=False, max_digits=10, decimal_places=2
    )
    cod = serializers.DecimalField(
        write_only=True, required=False, max_digits=10, decimal_places=2
    )
    riderId = serializers.CharField(write_only=True, required=False, allow_blank=True)
    merchantId = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    # Route stats
    distance_km = serializers.DecimalField(
        write_only=True, required=False, max_digits=10, decimal_places=2
    )
    duration_minutes = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        from orders.models import Order

        model = Order
        fields = [
            "id",
            "pickup",
            "dropoff",
            "senderName",
            "senderPhone",
            "receiverName",
            "receiverPhone",
            "vehicle",
            "packageType",
            "price",
            "cod",
            "riderId",
            "merchantId",
            "distance_km",
            "duration_minutes",
        ]

    def create(self, validated_data):
        from orders.models import Order, Delivery, Vehicle
        from .models import Rider
        from authentication.models import User

        # Extract non-model fields
        pickup = validated_data.pop("pickup")
        dropoff = validated_data.pop("dropoff")
        sender_name = validated_data.pop("senderName")
        sender_phone = validated_data.pop("senderPhone")
        receiver_name = validated_data.pop("receiverName")
        receiver_phone = validated_data.pop("receiverPhone")
        vehicle_name = validated_data.pop("vehicle")
        package_type = validated_data.pop("packageType")
        price = validated_data.get("price")
        # cod = validated_data.get("cod") # Unused
        rider_id = validated_data.get("riderId")
        merchant_id = validated_data.get("merchantId")
        distance_km = validated_data.get("distance_km")
        duration_minutes = validated_data.get("duration_minutes")

        # Resolve Vehicle
        vehicle_obj = Vehicle.objects.filter(name__iexact=vehicle_name).first()
        if not vehicle_obj:
            vehicle_obj = Vehicle.objects.first()

        # Resolve Rider
        rider_obj = None
        if rider_id:
            rider_obj = Rider.objects.filter(id=rider_id).first()

        # Resolve User (Merchant or Request User)
        order_user = self.context["request"].user
        if merchant_id:
            # Try to find merchant by profile id (6 chars) or user id (uuid)
            # The frontend sends the 6-char ID usually if using the dropdown which likely uses the proper ID
            # But wait, Merchant object in frontend has `id` (6 chars) and `userId` (UUID).
            # Let's check how we want to look it up.
            # If we send the UUID (userId), it's a direct User lookup.
            # If we send the 6-char ID, we need to look up via Merchant profile.
            # Let's assume we might send the 6-char ID.
            from .models import Merchant as MerchantProfile

            try:
                profile = MerchantProfile.objects.filter(
                    merchant_id=merchant_id
                ).first()
                if profile:
                    order_user = profile.user
            except Exception:
                pass

        # Calculate Price
        total_amount = price if price else vehicle_obj.base_price

        # Create Order
        order = Order.objects.create(
            user=order_user,
            pickup_address=pickup,
            sender_name=sender_name,
            sender_phone=sender_phone,
            vehicle=vehicle_obj,
            total_amount=total_amount,
            rider=rider_obj,
            status="Assigned" if rider_obj else "Pending",
            distance_km=distance_km,
            duration_minutes=duration_minutes,
        )

        # Create Delivery
        Delivery.objects.create(
            order=order,
            dropoff_address=dropoff,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            package_type=package_type,
        )

        return order


class MerchantSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="merchant_profile.merchant_id", read_only=True)
    userId = serializers.CharField(source="id", read_only=True)
    name = serializers.SerializerMethodField()
    contact = serializers.SerializerMethodField()
    phone = serializers.CharField(read_only=True)
    category = serializers.SerializerMethodField()
    totalOrders = serializers.SerializerMethodField()
    monthOrders = serializers.SerializerMethodField()
    walletBalance = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    joined = serializers.DateTimeField(
        source="created_at", format="%b %Y", read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "userId",
            "name",
            "contact",
            "phone",
            "category",
            "totalOrders",
            "monthOrders",
            "walletBalance",
            "status",
            "joined",
        ]

    def get_name(self, obj):
        return obj.business_name or "Unknown Business"

    def get_contact(self, obj):
        return obj.contact_name or "Unknown Contact"

    def get_category(self, obj):
        return "Retail"  # Mock

    def get_totalOrders(self, obj):
        return obj.orders.count()

    def get_monthOrders(self, obj):
        from django.utils import timezone

        now = timezone.now()
        return obj.orders.filter(
            created_at__month=now.month, created_at__year=now.year
        ).count()

    def get_walletBalance(self, obj):
        return 0  # Mock

    def get_status(self, obj):
        return "Active" if obj.is_active else "Inactive"
