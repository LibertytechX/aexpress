from rest_framework import serializers
from .models import Rider, DispatcherProfile, ActivityFeed, Zone, RelayNode
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


class DispatcherListSerializer(serializers.ModelSerializer):
    """Read-only serializer for listing dispatcher profiles."""

    name = serializers.SerializerMethodField()
    phone = serializers.CharField(source="user.phone", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    role = serializers.SerializerMethodField()
    joined = serializers.DateTimeField(
        source="created_at", format="%Y-%m-%d", read_only=True
    )
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)

    class Meta:
        model = DispatcherProfile
        fields = ["id", "name", "phone", "email", "role", "joined", "is_active"]

    def get_name(self, obj):
        return (
            obj.user.contact_name
            or f"{obj.user.first_name} {obj.user.last_name}".strip()
            or obj.user.phone
        )

    def get_role(self, obj):
        return "Dispatcher"


class DispatcherCreateSerializer(serializers.Serializer):
    """Write serializer: create a User with usertype=Dispatcher and its DispatcherProfile."""

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=6, write_only=True, style={"input_type": "password"}
    )

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        first_name = validated_data["first_name"]
        last_name = validated_data["last_name"]
        user = User.objects.create_user(
            phone=validated_data["phone"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
            contact_name=f"{first_name} {last_name}".strip(),
            usertype="Dispatcher",
        )
        profile = DispatcherProfile.objects.create(user=user)
        return profile


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
            "current_latitude",
            "current_longitude",
            "last_location_update",
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

    # Relay routing (async)
    routing_status = serializers.CharField(read_only=True)
    routing_error = serializers.CharField(read_only=True)
    is_relay_order = serializers.BooleanField(read_only=True)
    relay_legs_count = serializers.IntegerField(read_only=True)
    suggested_rider_id = serializers.CharField(
        source="suggested_rider.id", read_only=True, allow_null=True
    )

    pickup_lat = serializers.SerializerMethodField()
    pickup_lng = serializers.SerializerMethodField()
    dropoff_lat = serializers.SerializerMethodField()
    dropoff_lng = serializers.SerializerMethodField()

    relay_legs = serializers.SerializerMethodField()

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
            # Relay routing details (populated for relay orders)
            "is_relay_order",
            "routing_status",
            "routing_error",
            "relay_legs_count",
            "suggested_rider_id",
            "pickup_lat",
            "pickup_lng",
            "dropoff_lat",
            "dropoff_lng",
            "relay_legs",
        ]

    def get_pickup_lat(self, obj):
        return obj.pickup_latitude

    def get_pickup_lng(self, obj):
        return obj.pickup_longitude

    def get_dropoff_lat(self, obj):
        first = obj.deliveries.first()
        return getattr(first, "dropoff_latitude", None) if first else None

    def get_dropoff_lng(self, obj):
        first = obj.deliveries.first()
        return getattr(first, "dropoff_longitude", None) if first else None

    def get_relay_legs(self, obj):
        """Always include relay legs so the map survives list refreshes."""
        return OrderLegSerializer(
            obj.legs.all().order_by("leg_number"), many=True, context=self.context
        ).data

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
        order_map = {
            "Pending": "Pending",
            "Assigned": "Assigned",
            "Started": "In Transit",
            "Done": "Delivered",
            "CustomerCanceled": "Cancelled",
            "RiderCanceled": "Cancelled",
            "Failed": "Failed",
        }
        order_status = order_map.get(obj.status, "Pending")

        # If the Order-level status hasn't advanced past Assigned, check the
        # Delivery's own status so changes made there are reflected here too.
        if order_status in ("Pending", "Assigned"):
            first = obj.deliveries.first()
            if first:
                delivery_map = {
                    "InTransit": "In Transit",
                    "Delivered": "Delivered",
                    "Failed": "Failed",
                    "Canceled": "Cancelled",
                }
                delivery_status = delivery_map.get(first.status)
                if delivery_status:
                    return delivery_status

        return order_status

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

    # Optional lat/lng to skip geocoding
    pickup_lat = serializers.FloatField(
        write_only=True, required=False, allow_null=True
    )
    pickup_lng = serializers.FloatField(
        write_only=True, required=False, allow_null=True
    )
    dropoff_lat = serializers.FloatField(
        write_only=True, required=False, allow_null=True
    )
    dropoff_lng = serializers.FloatField(
        write_only=True, required=False, allow_null=True
    )

    # Relay
    is_relay_order = serializers.BooleanField(
        write_only=True, required=False, default=False
    )

    class Meta:
        from orders.models import Order

        model = Order
        fields = [
            "id",
            "pickup",
            "dropoff",
            "pickup_lat",
            "pickup_lng",
            "dropoff_lat",
            "dropoff_lng",
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
            "is_relay_order",
        ]

    def create(self, validated_data):
        from orders.models import Order, Delivery, Vehicle
        from .models import Rider
        from authentication.models import User

        # Extract non-model fields
        pickup = validated_data.pop("pickup")
        dropoff = validated_data.pop("dropoff")
        pickup_lat = validated_data.pop("pickup_lat", None)
        pickup_lng = validated_data.pop("pickup_lng", None)
        dropoff_lat = validated_data.pop("dropoff_lat", None)
        dropoff_lng = validated_data.pop("dropoff_lng", None)
        is_relay_order = validated_data.pop("is_relay_order", False)
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
            pickup_latitude=pickup_lat,
            pickup_longitude=pickup_lng,
            sender_name=sender_name,
            sender_phone=sender_phone,
            vehicle=vehicle_obj,
            total_amount=total_amount,
            rider=rider_obj,
            status="Assigned" if rider_obj else "Pending",
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            is_relay_order=is_relay_order,
            routing_status=(
                Order.RoutingStatus.PENDING
                if is_relay_order
                else Order.RoutingStatus.READY
            ),
            routing_error="",
            suggested_rider=None,
        )

        # Create Delivery
        Delivery.objects.create(
            order=order,
            pickup_address=pickup,
            pickup_latitude=pickup_lat,
            pickup_longitude=pickup_lng,
            sender_name=sender_name,
            sender_phone=sender_phone,
            dropoff_address=dropoff,
            dropoff_latitude=dropoff_lat,
            dropoff_longitude=dropoff_lng,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            package_type=package_type,
        )

        return order


class RelayNodeMiniSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import RelayNode

        model = RelayNode
        fields = ["id", "name", "latitude", "longitude", "zone"]


class OrderLegSerializer(serializers.ModelSerializer):
    start_relay_node = RelayNodeMiniSerializer(read_only=True)
    end_relay_node = RelayNodeMiniSerializer(read_only=True)
    rider_id = serializers.CharField(source="rider.id", read_only=True, allow_null=True)

    class Meta:
        from orders.models import OrderLeg

        model = OrderLeg
        fields = [
            "id",
            "leg_number",
            "status",
            "hub_pin",
            "distance_km",
            "duration_minutes",
            "rider_payout",
            "zone_compliance_bonus",
            "rider_id",
            "start_relay_node",
            "end_relay_node",
        ]


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
    joined = serializers.DateTimeField(source="created_at", read_only=True)

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


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import SystemSettings

        model = SystemSettings
        fields = "__all__"


class RiderOnboardingSerializer(serializers.Serializer):
    # User fields
    email = serializers.EmailField()
    phone = serializers.CharField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(
        required=False,
        write_only=True,
        min_length=6,
        style={"input_type": "password"},
        help_text="If omitted a random password is generated and e-mailed to the rider.",
    )
    is_verified = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Mark phone and email as verified immediately.",
    )

    # Rider Profile fields
    bank_name = serializers.CharField(required=False, max_length=100)
    bank_account_number = serializers.CharField(required=False, max_length=20)
    bank_routing_code = serializers.CharField(required=False, max_length=20)
    vehicle_type = serializers.PrimaryKeyRelatedField(
        queryset=serializers.SerializerMethodField(), required=False
    )
    vehicle_model = serializers.CharField(required=False, max_length=100)
    vehicle_plate_number = serializers.CharField(required=False, max_length=20)
    vehicle_color = serializers.CharField(required=False, max_length=50)
    working_type = serializers.ChoiceField(
        choices=[("freelancer", "Freelancer"), ("full_time", "Full Time")],
        default="freelancer",
    )
    team = serializers.CharField(required=False, max_length=100, default="Main Team")
    emergency_phone = serializers.CharField(required=False, max_length=20)
    city = serializers.CharField(required=False, max_length=100)
    address = serializers.CharField(required=False)
    home_zone = serializers.PrimaryKeyRelatedField(
        queryset=Zone.objects.all(), required=False, allow_null=True,
        help_text="Relay network zone to assign this rider to.",
    )
    driving_license_number = serializers.CharField(required=False, max_length=50)
    national_id = serializers.CharField(required=False, max_length=50)

    # Image fields (accepted as files from the frontend)
    avatar = serializers.ImageField(required=False)
    vehicle_photo = serializers.ImageField(required=False)
    driving_license_photo = serializers.ImageField(required=False)
    identity_card_photo = serializers.ImageField(required=False)

    def validate_email(self, value):
        from authentication.models import User

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone(self, value):
        from authentication.models import User

        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return value

    def __init__(self, *args, **kwargs):
        from orders.models import Vehicle

        super().__init__(*args, **kwargs)
        self.fields["vehicle_type"].queryset = Vehicle.objects.all()

    def create(self, validated_data):
        import string
        import random
        from .tasks import send_onboarding_email_task
        from authentication.models import User

        # Extract user data
        email = validated_data.pop("email")
        phone = validated_data.pop("phone")
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")
        is_verified = validated_data.pop("is_verified", False)

        # Use provided password or generate a random one
        password = validated_data.pop("password", None)
        if not password:
            password = "".join(
                random.choices(string.ascii_letters + string.digits, k=8)
            )

        from django.db import IntegrityError

        try:
            # Create User
            user = User.objects.create_user(
                phone=phone,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                contact_name=f"{first_name} {last_name}",
                usertype="Rider",
            )
            # Optionally mark as verified
            if is_verified:
                user.phone_verified = True
                user.email_verified = True
                user.save(update_fields=["phone_verified", "email_verified"])
        except IntegrityError as e:
            if "phone" in str(e).lower():
                raise serializers.ValidationError(
                    {"phone": "A user with this phone number already exists."}
                )
            if "email" in str(e).lower():
                raise serializers.ValidationError(
                    {"email": "A user with this email already exists."}
                )
            raise serializers.ValidationError(
                "An error occurred while creating the user."
            )

        # Create Rider Profile
        rider = Rider.objects.create(user=user, **validated_data)

        # Trigger Background Task for Email
        send_onboarding_email_task.delay(
            email=email, first_name=first_name, password=password, rider_id=rider.id
        )

        # Handle Document Uploads (Base64 for Celery)
        import base64

        avatar_data = None
        avatar_name = None
        if "avatar" in validated_data:
            avatar_file = validated_data.pop("avatar")
            avatar_data = base64.b64encode(avatar_file.read()).decode("utf-8")
            avatar_name = avatar_file.name

        vehicle_photo_data = None
        vehicle_photo_name = None
        if "vehicle_photo" in validated_data:
            vehicle_photo_file = validated_data.pop("vehicle_photo")
            vehicle_photo_data = base64.b64encode(vehicle_photo_file.read()).decode(
                "utf-8"
            )
            vehicle_photo_name = vehicle_photo_file.name

        license_data = None
        license_name = None
        if "driving_license_photo" in validated_data:
            license_file = validated_data.pop("driving_license_photo")
            license_data = base64.b64encode(license_file.read()).decode("utf-8")
            license_name = license_file.name

        id_data = None
        id_name = None
        if "identity_card_photo" in validated_data:
            id_file = validated_data.pop("identity_card_photo")
            id_data = base64.b64encode(id_file.read()).decode("utf-8")
            id_name = id_file.name

        from .tasks import upload_rider_documents_to_s3

        upload_rider_documents_to_s3.delay(
            rider_id=rider.id,
            avatar_data=avatar_data,
            avatar_name=avatar_name,
            vehicle_photo_data=vehicle_photo_data,
            vehicle_photo_name=vehicle_photo_name,
            driving_license_photo_data=license_data,
            driving_license_photo_name=license_name,
            identity_card_photo_data=id_data,
            identity_card_photo_name=id_name,
        )

        return rider


class ActivityFeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityFeed
        fields = [
            "id",
            "event_type",
            "order_id",
            "text",
            "color",
            "metadata",
            "created_at",
        ]


class ZoneSerializer(serializers.ModelSerializer):
    relay_nodes_count = serializers.SerializerMethodField()

    class Meta:
        model = Zone
        fields = [
            "id",
            "name",
            "center_lat",
            "center_lng",
            "radius_km",
            "is_active",
            "relay_nodes_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_relay_nodes_count(self, obj):
        return obj.relay_nodes.count()


class RelayNodeSerializer(serializers.ModelSerializer):
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
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
