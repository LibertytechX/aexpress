from rest_framework import serializers
from .models import (
    Rider,
    DispatcherProfile,
    ActivityFeed,
    Zone,
    ZoneTarget,
    RelayNode,
    VehicleAsset,
    Vertical,
)
from authentication.serializers import UserSerializer
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.cache import cache
from .models import VehicleTracking

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
        return obj.get_role_display()


class DispatcherCreateSerializer(serializers.Serializer):
    """Write serializer: create a User with usertype=Dispatcher and its DispatcherProfile."""

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=6, write_only=True, style={"input_type": "password"}
    )
    role = serializers.ChoiceField(
        choices=DispatcherProfile.Role.choices,
        default=DispatcherProfile.Role.ADMIN,
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
        role = validated_data.get("role", DispatcherProfile.Role.ADMIN)
        user = User.objects.create_user(
            phone=validated_data["phone"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
            contact_name=f"{first_name} {last_name}".strip(),
            usertype="Dispatcher",
        )
        profile = DispatcherProfile.objects.create(user=user, role=role)
        return profile


class RiderSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.contact_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)

    # Zone derived from hub (RelayNode) → zone FK
    zone = serializers.SerializerMethodField()

    # Hub field (maps to the rider's assigned relay node)
    hub = serializers.PrimaryKeyRelatedField(
        queryset=RelayNode.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    # Vehicle fields from Rider model
    vehicle = serializers.SerializerMethodField()

    # Assigned vehicle asset details
    vehicle_asset_detail = serializers.SerializerMethodField()

    # Mock/Computed fields to match frontend interface
    current_order = serializers.SerializerMethodField()
    todayOrders = serializers.SerializerMethodField()
    todayEarnings = serializers.SerializerMethodField()
    completionRate = serializers.IntegerField(default=98, read_only=True)
    avgTime = serializers.CharField(default="25 mins", read_only=True)
    joined = serializers.DateTimeField(
        source="created_at", format="%Y-%m-%d", read_only=True
    )
    total_yesterday_order_distance = serializers.SerializerMethodField()

    class Meta:
        model = Rider
        fields = [
            "id",
            "rider_id",
            "name",
            "phone",
            "hub",
            "zone",
            "vehicle",
            "vehicle_asset_detail",
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
            "total_yesterday_order_distance",
        ]

    def get_zone(self, obj):
        if obj.hub and obj.hub.zone_id:
            return str(obj.hub.zone_id)
        return None

    def get_todayOrders(self, obj):
        today = datetime.now().date()
        return obj.rider_orders.filter(status="Done", created_at__date=today).count()

    def get_todayEarnings(self, obj):
        from django.db.models import Sum

        today = datetime.now().date()
        total = obj.rider_orders.filter(
            status="Done", created_at__date=today
        ).aggregate(total=Sum("total_amount"))["total"]
        return float(total) if total else 0

    def get_current_order(self, obj):
        active_order = (
            obj.rider_orders.filter(
                status__in=["Assigned", "PickedUp", "Started", "Arrived", "Done"]
            )
            .order_by("-updated_at")
            .first()
        )
        if active_order:
            return active_order.order_number
        return None

    def get_total_yesterday_order_distance(self, obj):
        yesterday = datetime.now() - timedelta(days=1)
        cache_key = (
            f"total_yesterday_order_distance_{obj.id}_{yesterday.strftime('%Y-%m-%d')}"
        )

        cached_distance = cache.get(cache_key)
        if cached_distance is not None:
            return cached_distance

        # get the riders yesterdays order
        orders = obj.rider_orders.filter(created_at__date=yesterday.date())
        total_distance = 0
        for order in orders:
            if order.distance_km is not None:
                total_distance += order.distance_km

        # cache for 24 hours
        cache.set(cache_key, total_distance, 60 * 60 * 24)
        return total_distance

    def get_vehicle(self, obj):
        if obj.vehicle_type:
            return obj.vehicle_type.name
        return "None"

    def get_vehicle_asset_detail(self, obj):
        va = obj.vehicle_asset
        if not va:
            return None
        return {
            "id": str(va.id),
            "asset_id": va.asset_id,
            "plate_number": va.plate_number,
            "make": va.make,
            "model": va.model,
            "vehicle_type": va.vehicle_type,
            "color": va.color,
            "year": va.year,
        }


class OrderEventSerializer(serializers.ModelSerializer):
    event_type = serializers.CharField(source="event", read_only=True)
    created_by = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        from orders.models import OrderEvent

        model = OrderEvent
        fields = ["event_type", "old_value", "new_value", "created_by", "created_at"]

    def get_created_by(self, obj):
        if obj.created_by is None:
            return None
        user = obj.created_by
        name = (
            getattr(user, "get_full_name", lambda: "")()
            or getattr(user, "business_name", None)
            or getattr(user, "contact_name", None)
            or user.username
        )
        return name.strip() or user.username


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
    collect_on_delivery = serializers.BooleanField(read_only=True)

    # Extra fields for backward compatibility or extra detail
    items = serializers.SerializerMethodField()
    cod = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    timeline = serializers.SerializerMethodField()
    price_per_km = serializers.SerializerMethodField()
    events = OrderEventSerializer(many=True, read_only=True)

    waiting_time = serializers.SerializerMethodField()
    delivery_time = serializers.SerializerMethodField()
    total_order_time = serializers.SerializerMethodField()

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
    charge = serializers.SerializerMethodField()
    parent_order_number = serializers.CharField(
        source="parent_order.order_number", read_only=True, allow_null=True
    )
    sub_order_numbers = serializers.SerializerMethodField()
    sub_orders = serializers.SerializerMethodField()
    vertical_lead_name = serializers.SerializerMethodField()

    def get_sub_order_numbers(self, obj):
        """Return list of sub-order order_numbers if this is a relay or grouped parent order."""
        if not obj.parent_order_id:
            order_field = "relay_leg_number" if obj.is_relay_order else "created_at"
            return list(
                obj.sub_orders.values_list("order_number", flat=True).order_by(
                    order_field
                )
            )
        return []

    def get_sub_orders(self, obj):
        """Return simplified sub-order details if this is a relay or grouped parent order."""
        is_parent = not obj.parent_order_id
        if (obj.is_relay_order or obj.mode == "grouped") and is_parent:
            order_field = "relay_leg_number" if obj.is_relay_order else "created_at"
            sub_orders = obj.sub_orders.all().order_by(order_field)
            return [
                {
                    "id": so.order_number,
                    "status": so.status,
                    "rider": (
                        so.rider.user.contact_name
                        if so.rider and getattr(so.rider, "user", None)
                        else None
                    ),
                    "riderId": so.rider.rider_id if so.rider else None,
                    "created": (
                        so.created_at.strftime("%Y-%m-%d %H:%M")
                        if getattr(so, "created_at", None)
                        else None
                    ),
                    "amount": (
                        float(so.total_amount)
                        if getattr(so, "total_amount", None)
                        else 0.0
                    ),
                    "relay_leg_number": so.relay_leg_number,
                }
                for so in sub_orders
            ]
        return []

    def get_vertical_lead_name(self, obj):
        return obj.vertical_lead_name

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
            "mode",
            "amount",
            "distance",
            "time",
            "created",
            "cod",
            "codFee",
            "collect_on_delivery",
            "payment",
            "items",
            "vertical_lead_name",
            "pkg",
            "notes",
            "timeline",
            "customer",
            "payment_info",
            "is_partner_order",
            "partner_order_count",
            "day_returned_count",
            "rider_completed_count",
            "file_uploaded_urls",
            "customerPhone",
            "vehicle",
            "payment_status",
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
            "price_per_km",
            "events",
            "waiting_time",
            "delivery_time",
            "total_order_time",
            "charge",
            # Sub-order linkage
            "parent_order_number",
            "relay_leg_number",
            "sub_order_numbers",
            "sub_orders",
            "dispatcher_assigned",
            "source",
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
        vehicle = getattr(obj, "vehicle", None)
        try:
            return vehicle.name if vehicle else "Bike"
        except Exception:
            return "Bike"

    def get_pkg(self, obj):
        first = obj.deliveries.first()
        return first.package_type if first else "Box"

    def get_codFee(self, obj):
        return 0

    def get_status(self, obj):
        order_map = {
            "Pending": "Pending",
            "Assigned": "Assigned",
            "PickedUp": "Picked Up",  # rider app can set this directly
            "Started": "In Transit",
            "Arrived": "At Dropoff",  # rider is at the dropoff location
            "Done": "Delivered",
            "CustomerCanceled": "Cancelled",
            "RiderCanceled": "Cancelled",
            "Failed": "Failed",
        }
        order_status = order_map.get(obj.status, "Pending")

        # Safety fallback: if the Delivery record has advanced further than the
        # Order (e.g. rider-app update vs dispatcher update out of sync), prefer
        # the more advanced delivery status.  Covers Pending, Assigned, and
        # In Transit so a rider-completed delivery surfaces as "Delivered" even
        # when Order.status is still "Started".
        if order_status in ("Pending", "Assigned", "In Transit"):
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
        if obj.collect_on_delivery and obj.cod_amount:
            return float(obj.cod_amount)
        return 0

    def get_payment(self, obj):
        method_map = {
            "wallet": "Wallet",
            "cash_on_pickup": "Cash on Pickup",
            "receiver_pays": "Receiver Pays",
        }
        return method_map.get(obj.payment_method, "Wallet")

    def get_distance(self, obj):
        # Frontend expects a human-readable string.
        # Persisted at create time (from frontend-calculated routing) on Order.distance_km.
        val = getattr(obj, "distance_km", None)
        if val is None:
            return None
        try:
            km = Decimal(str(val))
        except Exception:
            return None
        return f"{km:.2f} km"

    def get_time(self, obj):
        val = getattr(obj, "duration_minutes", None)
        if val is None:
            return None
        try:
            minutes = int(val)
        except Exception:
            return None
        return f"{minutes} mins"

    def get_price_per_km(self, obj):
        """Effective rate: total_amount / distance_km, rounded to 2 dp.

        Returns None if distance_km is missing or zero so the frontend
        can display a dash instead of a nonsensical number.
        """
        try:
            dist = Decimal(str(obj.distance_km))
            if dist <= 0:
                return None
            rate = obj.total_amount / dist
            return float(rate.quantize(Decimal("0.01")))
        except Exception:
            return None

    def get_timeline(self, obj):
        return [{"time": obj.created_at.strftime("%H:%M"), "event": "Order Placed"}]

    def _format_timedelta(self, td):
        if not td:
            return None
        minutes = int(td.total_seconds() / 60)
        if minutes < 60:
            return f"{minutes} mins"
        else:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"

    def get_waiting_time(self, obj):
        if not getattr(obj, "assigned_at", None):
            return None
        return self._format_timedelta(obj.assigned_at - obj.created_at)

    def get_delivery_time(self, obj):
        if not getattr(obj, "assigned_at", None) or not getattr(
            obj, "completed_at", None
        ):
            return None
        return self._format_timedelta(obj.completed_at - obj.assigned_at)

    def get_total_order_time(self, obj):
        if not getattr(obj, "completed_at", None):
            return None
        return self._format_timedelta(obj.completed_at - obj.created_at)

    def get_charge(self, obj):
        charge = obj.charges.first()
        if charge:
            return {
                "amount": float(charge.amount),
                "status": charge.status,
                "created_at": charge.created_at.isoformat(),
            }
        return None


class OrderPriceUpdateSerializer(serializers.Serializer):
    """Write serializer for dispatcher price edits (Order.total_amount).

    Frontend uses `amount`. For backward-compatibility we also accept `price`.
    """

    amount = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2, min_value=Decimal("0")
    )
    price = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2, min_value=Decimal("0")
    )

    def validate(self, attrs):
        amt = attrs.get("amount")
        price = attrs.get("price")
        if amt is None and price is None:
            raise serializers.ValidationError(
                {"amount": "Provide 'amount' (or legacy 'price')."}
            )

        val = amt if amt is not None else price
        # Normalize to 2dp in case caller sends integer/float-ish decimal.
        try:
            val = Decimal(str(val)).quantize(Decimal("0.01"))
        except Exception:
            # DecimalField normally prevents this, but keep a friendly error.
            raise serializers.ValidationError({"amount": "Invalid amount."})

        attrs["amount"] = val
        return attrs


class OrderCreateSerializer(serializers.ModelSerializer):
    # Input fields from Frontend
    pickup = serializers.CharField(write_only=True, required=False, allow_blank=True)
    dropoff = serializers.CharField(write_only=True, required=False, allow_blank=True)
    senderName = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    senderPhone = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    receiverName = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    receiverPhone = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    vehicle = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )  # "Bike", "Car", etc.
    packageType = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    price = serializers.DecimalField(
        write_only=True, required=False, max_digits=10, decimal_places=2
    )
    manual_price = serializers.BooleanField(
        write_only=True, required=False, default=False
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
    is_partner_order = serializers.BooleanField(
        write_only=True, required=False, default=False
    )
    partner_order_count = serializers.IntegerField(write_only=True, required=False)
    file_uploaded_urls = serializers.ListField(
        child=serializers.URLField(), required=False, default=list
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
            "manual_price",
            "cod",
            "riderId",
            "merchantId",
            "distance_km",
            "duration_minutes",
            "is_relay_order",
            "is_partner_order",
            "partner_order_count",
            "file_uploaded_urls",
            "payment_method",
        ]

    def create(self, validated_data):
        from orders.services import get_order_service

        order_service = get_order_service()
        return order_service.create_dispatcher_order(
            self.context["request"].user, validated_data
        )


class MerchantPricingOverrideSerializer(serializers.ModelSerializer):
    """Upsert serializer for per-merchant/per-vehicle pricing overrides."""

    vehicle_name = serializers.CharField(source="vehicle.name", read_only=True)
    merchant_user_id = serializers.CharField(source="merchant.id", read_only=True)

    class Meta:
        from orders.models import MerchantPricingOverride

        model = MerchantPricingOverride
        fields = [
            "id",
            "merchant",
            "merchant_user_id",
            "vehicle",
            "vehicle_name",
            "flat_fee",
            "pricing_tiers",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        from orders.models import MerchantPricingOverride

        merchant = validated_data["merchant"]
        vehicle = validated_data["vehicle"]
        defaults = {
            k: v for k, v in validated_data.items() if k not in ("merchant", "vehicle")
        }
        obj, _ = MerchantPricingOverride.objects.update_or_create(
            merchant=merchant, vehicle=vehicle, defaults=defaults
        )
        return obj


class RelayNodeMiniSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import RelayNode

        model = RelayNode
        fields = ["id", "name", "latitude", "longitude", "zone"]


class OrderLegSerializer(serializers.ModelSerializer):
    start_relay_node = RelayNodeMiniSerializer(read_only=True)
    end_relay_node = RelayNodeMiniSerializer(read_only=True)
    rider_id = serializers.CharField(source="rider.id", read_only=True, allow_null=True)
    rider_name = serializers.CharField(
        source="rider.user.contact_name", read_only=True, allow_null=True
    )
    suggested_rider_id = serializers.CharField(
        source="suggested_rider.id", read_only=True, allow_null=True
    )
    suggested_rider_name = serializers.CharField(
        source="suggested_rider.user.contact_name", read_only=True, allow_null=True
    )
    sub_order_number = serializers.SerializerMethodField()

    def get_sub_order_number(self, obj):
        """Return the order_number of the sub-order created for this leg, if any."""
        from orders.models import Order

        try:
            sub = (
                Order.objects.filter(
                    parent_order=obj.order,
                    relay_leg_number=obj.leg_number,
                )
                .values_list("order_number", flat=True)
                .first()
            )
            return sub
        except Exception:
            return None

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
            "rider_name",
            "suggested_rider_id",
            "suggested_rider_name",
            "sub_order_number",
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
    isPartner = serializers.BooleanField(
        source="merchant_profile.is_partner", read_only=True
    )
    partnerBasePrice = serializers.DecimalField(
        source="merchant_profile.partner_base_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
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
            "isPartner",
            "partnerBasePrice",
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
    hub = serializers.PrimaryKeyRelatedField(
        queryset=RelayNode.objects.all(),
        required=False,
        allow_null=True,
        help_text="Relay hub (node) to assign this rider to.",
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
    vertical_name = serializers.CharField(source="vertical.name", read_only=True)

    class Meta:
        model = Zone
        fields = [
            "id",
            "name",
            "vertical",
            "vertical_name",
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


class ZoneTargetSerializer(serializers.ModelSerializer):
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
        """Ensure month is always the first day of the month."""
        return value.replace(day=1)


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


class VehicleAssetSerializer(serializers.ModelSerializer):
    assigned_rider = serializers.SerializerMethodField()
    # Sourced from the persisted model field so Ably real-time payloads include the
    # correct value without requiring a live ORM annotation on every publish.
    orders_today = serializers.DecimalField(
        source="deliveries_km_today",
        max_digits=10,
        decimal_places=2,
        read_only=True,
        default=0,
    )
    yesterday_distance = serializers.SerializerMethodField()

    class Meta:
        model = VehicleAsset
        fields = [
            "id",
            "asset_id",
            "plate_number",
            "vehicle_type",
            "make",
            "model",
            "year",
            "color",
            "vin",
            "photo",
            "insurance_expiry",
            "registration_expiry",
            "road_worthiness_expiry",
            "engine_status",
            "total_distance",
            "unit_of_distance",
            "distance_today",
            "orders_today",
            "stop_duration",
            "moved_timestamp",
            "latitude",
            "longitude",
            "course",
            "speed",
            "last_telemetry_at",
            "is_active",
            "assigned_rider",
            "created_at",
            "updated_at",
            "yesterday_distance",
        ]
        read_only_fields = ["id", "asset_id", "created_at", "updated_at"]

    def get_yesterday_distance(self, obj):

        yesterday = datetime.now() - timedelta(days=1)
        cache_key = f"yesterday_distance_{obj.id}_{yesterday.strftime('%Y-%m-%d')}"

        cached_distance = cache.get(cache_key)
        if cached_distance is not None:
            return cached_distance

        # get all yesterdays vehicle tracking entries
        trackings = VehicleTracking.objects.filter(
            vehicle_asset=obj, created_at__date=yesterday
        ).order_by("created_at")

        distance = 0
        if trackings.exists():
            first_entry = trackings.first()
            last_entry = trackings.last()
            distance = last_entry.travelled - first_entry.travelled

        # Cache for 24 hours
        cache.set(cache_key, distance, 60 * 60 * 24)
        return distance

    def get_assigned_rider(self, obj):
        # Prefer prefetch cache when VehicleAssetViewSet prefetches riders.
        rider = obj.riders.all().first()
        if rider:
            return {
                "id": str(rider.id),
                "rider_id": rider.rider_id,
                "name": rider.user.contact_name if rider.user else "Unknown",
                "phone": rider.user.phone if rider.user else "",
            }
        return None


class VerticalSerializer(serializers.ModelSerializer):
    zone_count = serializers.SerializerMethodField()

    class Meta:
        model = Vertical
        fields = [
            "id",
            "name",
            "code",
            "lead_name",
            "is_active",
            "zone_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_zone_count(self, obj):
        return obj.zones.count()
