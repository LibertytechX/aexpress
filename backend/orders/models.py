from decimal import Decimal
import random
import string
from typing import Optional
import uuid
from django.db import models
from django.utils import timezone
from authentication.models import User


class Vehicle(models.Model):
    """Vehicle types available for delivery."""

    name = models.CharField(max_length=50, unique=True)
    max_weight_kg = models.IntegerField()

    # Pricing structure
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Legacy flat rate (deprecated)"
    )
    base_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Base fare for any delivery",
    )
    rate_per_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Rate charged per kilometer",
    )
    rate_per_minute = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Rate charged per minute"
    )
    min_distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Minimum distance covered by base fare/min fee",
    )
    min_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Minimum fee charged for any trip",
    )
    pricing_tiers = models.JSONField(
        null=True,
        blank=True,
        help_text="Tiered pricing config, e.g. {type:'tiered', floor_km:6, floor_fee:1700, tiers:[{max_km:10,rate:275},...]}",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "vehicles"
        ordering = ["base_fare"]

    def __str__(self):
        return f"{self.name} - Base: ₦{self.base_fare} + ₦{self.rate_per_km}/km + ₦{self.rate_per_minute}/min"

    def calculate_fare(self, distance_km, duration_minutes):
        """
        Calculate total fare based on distance and duration.

        If the vehicle has ``pricing_tiers`` (JSON field), the tiered algorithm
        is used — this must match the frontend's ``calcTieredPrice`` exactly so
        the price the user sees during checkout equals the price stored on the
        order.

        Otherwise falls back to the legacy formula:
            base_fare + rate_per_km * dist + rate_per_minute * dur
        with ``min_fee`` as a floor.
        """
        from decimal import Decimal, ROUND_HALF_UP
        import math

        km = float(distance_km)

        # ── Tiered pricing (mirrors frontend calcTieredPrice) ──────────
        pt = self.pricing_tiers
        if pt and pt.get("type") == "tiered":
            floor_km = float(pt.get("floor_km", 0))
            floor_fee = float(pt.get("floor_fee", 0))
            tiers = pt.get("tiers") or []

            if km <= floor_km:
                return Decimal(str(floor_fee)).quantize(Decimal("0.01"))

            # Generic tiered pricing — select the tier by distance, apply rate × distance
            for tier in tiers:
                if not isinstance(tier, dict):
                    continue
                rate = float(tier.get("rate") or 0)
                max_km = tier.get("max_km")

                # Unbounded tier (or missing max) applies to any remaining distances
                if max_km is None or km <= float(max_km):
                    price = round(km * rate)
                    return Decimal(str(price)).quantize(Decimal("0.01"))

            # Fallback for unexpected tier config
            last_rate = float(tiers[-1].get("rate") or 0) if tiers else 0
            price = round(km * last_rate)
            return Decimal(str(price)).quantize(Decimal("0.01"))

        # ── Legacy formula ─────────────────────────────────────────────
        dist = Decimal(str(distance_km))
        min_dist = self.min_distance_km
        duration = Decimal(str(duration_minutes))

        base_calc_at_min = (
            self.base_fare
            + (min_dist * self.rate_per_km)
            + (duration * self.rate_per_minute)
        )
        effective_base = max(base_calc_at_min, self.min_fee)

        if dist > min_dist:
            excess_dist = dist - min_dist
            total = effective_base + (excess_dist * self.rate_per_km)
        else:
            total = max(
                self.base_fare
                + (dist * self.rate_per_km)
                + (duration * self.rate_per_minute),
                self.min_fee,
            )

        return total.quantize(Decimal("0.01"))


class MerchantPricingOverride(models.Model):
    """Optional per-merchant pricing override for a specific vehicle.

    Precedence (when is_active=True):
      1) flat_fee (if set)
      2) pricing_tiers (if set)
      3) fallback to Vehicle.calculate_fare()
    """

    merchant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="merchant_pricing_overrides",
        help_text="Merchant user this override applies to",
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="merchant_pricing_overrides",
    )

    # If set, this becomes the full delivery fee (ignores distance/duration/tiers)
    flat_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Flat per-ride fee (if set, ignores tiered pricing)",
    )

    # If set (and flat_fee is null), used instead of Vehicle.pricing_tiers
    pricing_tiers = models.JSONField(
        null=True,
        blank=True,
        help_text="Tiered pricing config (same shape as Vehicle.pricing_tiers)",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "merchant_pricing_overrides"
        # unique_together = [("merchant", "vehicle")]
        indexes = [
            models.Index(fields=["merchant", "vehicle"]),
            models.Index(fields=["merchant", "-created_at"]),
        ]

    def __str__(self):
        return f"Override: {self.merchant_id} × {self.vehicle.name}"


class Order(models.Model):
    """Main order model for delivery requests."""

    class RoutingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    MODE_CHOICES = [
        ("quick", "Quick Send"),
        ("multi", "Multi-Drop"),
        ("bulk", "Bulk Import"),
        ("grouped", "Grouped"),
    ]

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Assigned", "Assigned"),
        ("AssignmentAccepted", "Assignment Accepted"),
        ("AssignmentRejected", "Assignment Rejected"),
        ("Started", "Started"),
        ("Pickup", "Pick Up"),
        ("Fulfilling", "Fulfilling"),
        ("Arrived", "Arrived"),
        ("Done", "Done"),  # Delivered
        ("CustomerCanceled", "Customer Canceled"),
        ("RiderCanceled", "Rider Canceled"),
        ("Failed", "Failed"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("wallet", "Wallet"),
        ("cash", "Cash"),
        ("cash_on_pickup", "Cash on Pickup"),
        ("receiver_pays", "Receiver Pays"),
        ("postpaid", "Postpaid"),
        ("subscription", "Subscription"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Cancelled", "Cancelled"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
        ("Postpaid", "Postpaid"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rider_orders",
    )
    dispatcher_assigned = models.BooleanField(
        default=False,
        help_text="True if the rider was manually assigned by a dispatcher",
    )

    # Order details
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default="quick")
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT, related_name="orders"
    )
    partner = models.CharField(max_length=20, null=True, blank=True)
    is_partner_order = models.BooleanField(default=False)
    partner_order_count = models.PositiveIntegerField(null=True, blank=True)
    day_returned_count = models.PositiveIntegerField(null=True, blank=True)
    rider_completed_count = models.PositiveIntegerField(null=True, blank=True)
    file_uploaded_urls = models.JSONField(null=True, blank=True, default=list)
    # Pickup information
    pickup_address = models.TextField()
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)
    sender_name = models.CharField(max_length=255)
    sender_phone = models.CharField(max_length=20)

    # Payment
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default="wallet"
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Pending"
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Route information for pricing
    distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total distance in kilometers",
    )
    duration_minutes = models.IntegerField(
        null=True, blank=True, help_text="Total duration in minutes"
    )

    # Escrow tracking
    escrow_held = models.BooleanField(
        default=False, help_text="Whether funds are held in escrow"
    )
    escrow_released = models.BooleanField(
        default=False, help_text="Whether escrow funds have been released"
    )

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Pending", db_index=True
    )

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    scheduled_pickup_time = models.DateTimeField(null=True, blank=True)

    # For relay sub-orders: points back to the parent relay order that spawned this one.
    # Null for top-level (non-relay-sub) orders.
    parent_order = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_orders",
        help_text="Parent relay order that this sub-order belongs to (null for regular orders)",
    )
    # Which relay leg number this sub-order represents (0 = not a relay sub-order).
    relay_leg_number = models.PositiveSmallIntegerField(
        default=0,
        help_text="Leg number (1-based) within the parent relay route (0 for regular orders)",
    )

    # Relay delivery
    is_relay_order = models.BooleanField(
        default=False,
        help_text="True when this order is split into multiple relay legs",
    )
    relay_legs_count = models.IntegerField(
        default=0,
        help_text="Total number of relay legs (0 for standard single-rider orders)",
    )

    # Relay routing (async)
    routing_status = models.CharField(
        max_length=20,
        choices=RoutingStatus.choices,
        default=RoutingStatus.READY,
        db_index=True,
        help_text="Async relay routing status (only meaningful for relay orders)",
    )
    routing_error = models.TextField(
        blank=True,
        default="",
        help_text="Error details when relay routing fails",
    )
    suggested_rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suggested_for_orders",
        help_text="Suggested first-leg rider for relay orders",
    )

    # Cash on Delivery
    collect_on_delivery = models.BooleanField(
        default=False,
        help_text="Whether the rider should collect payment from the customer on behalf of the merchant",
    )
    cod_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount the rider should collect from the customer (COD)",
    )

    # Source detection
    SOURCE_CHOICES = [
        ("merchant_web", "Merchant Web"),
        ("dispatcher_web", "Dispatcher Web"),
    ]
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="merchant_web",
        help_text="Where the order was created from",
    )

    # SmartParcel locker delivery fields
    is_percel_order = models.BooleanField(
        default=False, help_text="True if this is a SmartParcel locker order"
    )
    is_pickup_percel = models.BooleanField(
        default=False, help_text="True if pickup is from a SmartParcel box"
    )
    isdelivery_percel = models.BooleanField(
        default=False, help_text="True if delivery is to a SmartParcel box"
    )
    percel_info = models.JSONField(
        null=True,
        blank=True,
        help_text="Full JSON response/info from SmartParcel for this order",
    )

    # Additional info
    notes = models.TextField(blank=True)
    payment_info = models.JSONField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at", "status"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    @property
    def vertical_lead_name(self) -> str | None:
        """Get the name of the vertical lead for this order."""
        if not (self.rider and self.rider.hub and self.rider.hub.zone_id):
            return None
        return self.rider.hub.zone.zone_lead.user.full_name

    def save(self, *args, **kwargs):
        """Generate order number if not exists."""
        if not self.order_number:
            # Generate order number: 6XXXXXX format
            last_order = Order.objects.order_by("-order_number").first()
            if last_order and last_order.order_number:
                try:
                    last_num = int(last_order.order_number)
                    self.order_number = str(last_num + 1)
                except ValueError:
                    self.order_number = str(6158000 + Order.objects.count() + 1)
            else:
                self.order_number = "6158000"

        super().save(*args, **kwargs)


class Delivery(models.Model):
    """Individual delivery/dropoff for an order (supports multi-drop)."""

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("InTransit", "In Transit"),
        ("Delivered", "Delivered"),
        ("Failed", "Failed"),
        ("Canceled", "Canceled"),
    ]

    PACKAGE_TYPE_CHOICES = [
        ("Box", "Box"),
        ("Envelope", "Envelope"),
        ("Fragile", "Fragile"),
        ("Food", "Food"),
        ("Document", "Document"),
        ("Other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="deliveries"
    )

    # Pickup information
    pickup_address = models.TextField(blank=True, default="")
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)
    sender_name = models.CharField(max_length=255, blank=True, default="")
    sender_phone = models.CharField(max_length=20, blank=True, default="")

    # Dropoff information
    dropoff_address = models.TextField()
    dropoff_latitude = models.FloatField(null=True, blank=True)
    dropoff_longitude = models.FloatField(null=True, blank=True)
    receiver_name = models.CharField(max_length=255)
    receiver_phone = models.CharField(max_length=20)

    # Package details
    package_type = models.CharField(
        max_length=20, choices=PACKAGE_TYPE_CHOICES, default="Box"
    )
    notes = models.TextField(blank=True)

    # Cash on delivery
    COD_FROM_CHOICES = [
        ("sender", "Sender"),
        ("customer", "Customer / Receiver"),
    ]
    cod_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cod_from = models.CharField(
        max_length=20, choices=COD_FROM_CHOICES, default="customer"
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    failure_reason = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Reason the delivery failed",
    )

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Sequence for multi-drop
    sequence = models.IntegerField(default=1)

    # Route details (locked in at order creation time)
    # For multi-drop orders this should represent the leg distance/time to reach
    # this stop (typically previous stop → this stop).
    distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Road distance in kilometers for this delivery leg",
    )
    duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Estimated duration in minutes for this delivery leg",
    )

    class Meta:
        db_table = "deliveries"
        ordering = ["order", "sequence"]
        indexes = [
            models.Index(fields=["order", "sequence"]),
        ]

    def __str__(self):
        return f"Delivery to {self.receiver_name} - Order {self.order.order_number}"


class OrderEvent(models.Model):
    """Event log for orders."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    event = models.CharField(max_length=100)
    description = models.TextField()

    # Structured values for auditable events (e.g. price_change)
    old_value = models.CharField(max_length=100, blank=True, default="")
    new_value = models.CharField(max_length=100, blank=True, default="")

    # Who triggered the event (nullable so existing rows are unaffected)
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_order_events",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_events"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event} for {self.order.order_number}"


class OrderLeg(models.Model):
    """
    A single hop in a relay delivery order.
    One Order (parent) has N OrderLegs, each assigned to a different rider.
    Packages are transferred at RelayNodes using hub-and-hold: the package
    waits at the relay hub until the next rider picks up.
    """

    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        ASSIGNED = "Assigned", "Assigned"
        PICKED_UP = "PickedUp", "Picked Up"
        IN_TRANSIT = "InTransit", "In Transit"
        AT_HUB = "AtHub", "At Hub"  # package dropped, waiting for next rider
        COMPLETED = "Completed", "Completed"
        FAILED = "Failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="legs")
    leg_number = models.PositiveIntegerField(
        help_text="Sequential leg number starting at 1"
    )

    # Rider assigned to this leg
    rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="relay_legs",
    )

    # Nearest available rider suggested at route-generation time for this leg
    suggested_rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suggested_legs",
        help_text="Nearest authorized rider suggested for this leg at generation time",
    )

    # Relay handoff points
    # Null start_relay_node  → first leg, picks up at order.pickup_address
    # Null end_relay_node    → last leg, delivers to order delivery address
    start_relay_node = models.ForeignKey(
        "dispatcher.RelayNode",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="outgoing_legs",
        help_text="Null for first leg (pickup from order origin)",
    )
    end_relay_node = models.ForeignKey(
        "dispatcher.RelayNode",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="incoming_legs",
        help_text="Null for last leg (delivers to order destination)",
    )

    # Route details (locked in at order creation time)
    distance_km = models.FloatField(default=0.0, help_text="Road distance for this leg")
    duration_minutes = models.IntegerField(default=0)

    # Settlement — pre-calculated so rider knows earnings before accepting
    # Formula: (leg_distance_km / sum_all_legs_distance_km) × total_rider_pool
    rider_payout = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Pre-calculated payout amount for this leg",
    )
    zone_compliance_bonus = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Bonus applied when rider stays within their assigned zone path",
    )

    # 6-digit PIN used by hub agent to release package to the next rider
    hub_pin = models.CharField(
        max_length=6,
        blank=True,
        default="",
        help_text="PIN generated at leg creation; hub agent confirms before handoff",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Timestamps
    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    dropped_at_hub_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_legs"
        ordering = ["order", "leg_number"]
        unique_together = [("order", "leg_number")]

    def __str__(self):
        return f"Order {self.order.order_number} — Leg {self.leg_number}"

    def save(self, *args, **kwargs):
        if not self.hub_pin:
            self.hub_pin = "".join(random.choices(string.digits, k=6))
        super().save(*args, **kwargs)


class MerchantPriceList(models.Model):
    """
    Container for a set of destination pricing rules (manual tariffs).
    A merchant can have one active list per vehicle type.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="merchant_pricelists",
        help_text="Merchant user this list belongs to",
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="merchant_pricelists",
        help_text="The vehicle type this price list applies to",
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name for the list, e.g. 'Goldplates Chevron Pricing'",
    )
    is_active = models.BooleanField(
        default=True, help_text="Inactive lists are ignored during fare calculation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "merchant_pricelists"
        unique_together = ["merchant", "vehicle"]

    def __str__(self):
        return f"{self.name} — {self.merchant.business_name or self.merchant.phone}"


class MerchantPriceListItem(models.Model):
    """
    Individual rows (distance buckets) within a MerchantPriceList.
    Defines a fixed fee for a specific distance range.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    price_list = models.ForeignKey(
        MerchantPriceList,
        on_delete=models.CASCADE,
        related_name="items",
    )
    label = models.CharField(
        max_length=255,
        help_text="Human-readable destination or bucket name (e.g. 'Agungi')",
    )
    min_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Starting distance for this bucket (inclusive)",
    )
    max_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Ending distance for this bucket (inclusive)",
    )
    fixed_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The total fee to be charged for this range",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "merchant_pricelist_items"
        ordering = ["min_km"]

    def __str__(self):
        return f"{self.label}: {self.min_km}-{self.max_km}km = ₦{self.fixed_fee}"


class GoogleAutoCompleteSessionUsage(models.Model):
    """Tracks Google Places Autocomplete session usage and billing lifecycle."""

    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        EXPIRED = "EXPIRED", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_token = models.CharField(
        max_length=500,
        unique=True,
        db_index=True,
        help_text="Unique session token for the autocomplete session",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="google_autocomplete_session_usages",
        help_text="User or merchant associated with this session",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
        db_index=True,
        help_text="Session status: IN_PROGRESS, RESOLVED, or EXPIRED",
    )
    price_per_session = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0.0050"),
        help_text="Cost per autocomplete session in USD ($0.005)",
    )
    request_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of autocomplete query hits within this session",
    )
    place_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Google Place ID resolved for this session",
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when place details was resolved",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "google_autocomplete_session_usages"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"GoogleAutoCompleteSession {self.session_token} [{self.status}] - hits: {self.request_count}"

    def mark_resolved(self, place_id: str) -> None:
        """Mark session as resolved with the selected place ID.

        Args:
            place_id: The Google Place ID returned upon place selection.
        """
        self.status = self.Status.RESOLVED
        self.place_id = place_id
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "place_id", "resolved_at", "updated_at"])

    def mark_expired(self) -> None:
        """Mark session as expired."""
        self.status = self.Status.EXPIRED
        self.save(update_fields=["status", "updated_at"])

    @classmethod
    def record_hit(
        cls, session_token: str, user: Optional[User] = None
    ) -> Optional["GoogleAutoCompleteSessionUsage"]:
        """Record an autocomplete hit for a session token.

        Creates a new session usage if it does not exist, or increments request_count
        if an in-progress session exists.

        Args:
            session_token: The unique UUID session token.
            user: Optional authenticated User/Merchant initiating the autocomplete.

        Returns:
            The created or updated GoogleAutoCompleteSessionUsage instance, or None.
        """
        if not session_token:
            return None

        usage = cls.objects.filter(session_token=session_token).first()
        if usage:
            if usage.status == cls.Status.IN_PROGRESS:
                usage.request_count = models.F("request_count") + 1
                if user and not usage.user:
                    usage.user = user
                    usage.save(update_fields=["request_count", "user", "updated_at"])
                else:
                    usage.save(update_fields=["request_count", "updated_at"])
                usage.refresh_from_db(fields=["request_count", "user"])
            return usage

        return cls.objects.create(
            session_token=session_token,
            user=user,
            status=cls.Status.IN_PROGRESS,
            price_per_session=Decimal("0.0050"),
            request_count=1,
        )

    @classmethod
    def expire_stale_sessions(cls, older_than_minutes: int = 30) -> int:
        """Mark sessions that have remained IN_PROGRESS longer than threshold as EXPIRED.

        Args:
            older_than_minutes: Threshold in minutes after which in-progress sessions expire.

        Returns:
            Number of sessions marked as EXPIRED.
        """
        cutoff = timezone.now() - timezone.timedelta(minutes=older_than_minutes)
        return cls.objects.filter(
            status=cls.Status.IN_PROGRESS,
            created_at__lte=cutoff,
        ).update(status=cls.Status.EXPIRED, updated_at=timezone.now())


class GooglePlace(models.Model):
    """Stores previously resolved Google Place details to minimize external API requests."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    place_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Google Place ID",
    )
    formatted_address = models.TextField(
        help_text="Formatted address string returned from Google",
    )
    lat = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        help_text="Latitude coordinate",
    )
    lng = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        help_text="Longitude coordinate",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "google_places"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.formatted_address} ({self.place_id})"
