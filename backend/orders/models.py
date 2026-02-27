import random
import string
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
        help_text="Tiered pricing config, e.g. {type:'tiered', floor_km:6, floor_fee:1700, tiers:[{max_km:10,rate:275},...]}"
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

            # Tier 0: e.g. ≤10 km → km × rate, floored at floor_fee
            if len(tiers) > 0 and (tiers[0].get("max_km") is None or km <= float(tiers[0]["max_km"])):
                price = max(round(km * float(tiers[0]["rate"])), floor_fee)
                return Decimal(str(price)).quantize(Decimal("0.01"))

            # Tier 1: e.g. ≤15 km → km × rate, floored at tier-0 boundary
            if len(tiers) > 1 and (tiers[1].get("max_km") is None or km <= float(tiers[1]["max_km"])):
                boundary = float(tiers[0].get("max_km", floor_km)) * float(tiers[0].get("rate", 0))
                price = max(round(km * float(tiers[1]["rate"])), round(boundary))
                return Decimal(str(price)).quantize(Decimal("0.01"))

            # Tier 2+: e.g. >15 km → km × rate, floored at tier-1 boundary
            if len(tiers) > 2:
                boundary = float(tiers[1].get("max_km", 0)) * float(tiers[1].get("rate", 0))
                price = max(round(km * float(tiers[2]["rate"])), round(boundary))
                return Decimal(str(price)).quantize(Decimal("0.01"))

            # Fallback for unexpected tier config
            last_rate = float(tiers[-1].get("rate", 0)) if tiers else 0
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
    ]

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Assigned", "Assigned"),
        ("PickedUp", "Picked Up"),
        ("Started", "Started"),
        ("Arrived", "Arrived"),
        ("Done", "Done"),
        ("CustomerCanceled", "Customer Canceled"),
        ("RiderCanceled", "Rider Canceled"),
        ("Failed", "Failed"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("wallet", "Wallet"),
        ("cash", "Cash"),
        ("cash_on_pickup", "Cash on Pickup"),
        ("receiver_pays", "Receiver Pays"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
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

    # Order details
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default="quick")
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT, related_name="orders"
    )

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
    picked_up_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    scheduled_pickup_time = models.DateTimeField(null=True, blank=True)

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

    # Additional info
    notes = models.TextField(blank=True)
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
        return f"Order {self.order_number} - {self.user.business_name}"

    def save(self, *args, **kwargs):
        """Generate order number if not exists."""
        if not self.order_number:
            # Generate order number: 6XXXXXX format
            last_order = Order.objects.order_by("-created_at").first()
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

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Sequence for multi-drop
    sequence = models.IntegerField(default=1)

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
        AT_HUB = "AtHub", "At Hub"         # package dropped, waiting for next rider
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
