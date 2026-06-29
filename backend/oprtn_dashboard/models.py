"""
Models for the Operations Dashboard app.

  - AlertType / Severity / EntityType / AlertStatus : shared enums (also used by
    the alert rules + engine in later phases).
  - Alert     (db_table="ops_alerts")      : one record per ongoing issue.
  - AlertRule (db_table="ops_alert_rules") : admin-editable thresholds so the
    engine has no hardcoded numbers.

Source of truth stays `orders.Order`; shared config lives on
`dispatcher.SystemSettings`. See AXPRESS_DASHBOARDS_IMPLEMENTATION_GUIDE.md §14.4.

NOTE: pure cost/margin alerts (LOW_MARGIN / NEGATIVE_PROFIT) are intentionally
omitted — they depend on the fuel/maintenance cost model, which is out of scope.
"""

import uuid

from django.db import models
from django.utils import timezone


class AlertType(models.TextChoices):
    # ── Rider integrity / behaviour ──────────────────────────────────
    BIKE_AFTER_HOURS = "BIKE_AFTER_HOURS", "Bike moving after hours"
    GHOST_RIDE = "GHOST_RIDE", "Ghost ride (offline but moving)"
    RIDER_IDLE = "RIDER_IDLE", "Rider idle (online, stationary)"
    SPEED_VIOLATION = "SPEED_VIOLATION", "Speed violation"
    LOW_ACCEPTANCE = "LOW_ACCEPTANCE", "Low offer-acceptance rate"
    RIDER_INACTIVITY = "RIDER_INACTIVITY", "Rider inactive (online, no orders)"
    LOW_CSAT = "LOW_CSAT", "Low CSAT rating"

    # ── Order lifecycle ──────────────────────────────────────────────
    INCOMPLETE_ORDER = "INCOMPLETE_ORDER", "Incomplete order (accepted, not done)"
    ORDER_STUCK = "ORDER_STUCK", "Order stuck (never started)"
    ORDER_DELAYED = "ORDER_DELAYED", "Order delayed (in transit too long)"
    HIGH_CANCELLATION = "HIGH_CANCELLATION", "High cancellation rate"
    RELAY_ROUTING_FAILURE = "RELAY_ROUTING_FAILURE", "Relay routing failure"

    # ── Financial / COD ──────────────────────────────────────────────
    COD_RETENTION = "COD_RETENTION", "COD retained (unremitted too long)"
    COD_GAP = "COD_GAP", "COD collection gap"
    COD_FEE_LEAKAGE = "COD_FEE_LEAKAGE", "COD fee leakage"
    PAYMENT_FAILURE_SPIKE = "PAYMENT_FAILURE_SPIKE", "Payment failure spike"
    HIGH_RIDER_PAYOUT = "HIGH_RIDER_PAYOUT", "High rider payout ratio"
    REVENUE_DROP = "REVENUE_DROP", "Revenue drop vs previous period"

    # ── Fleet / compliance / system ──────────────────────────────────
    INSURANCE_EXPIRING = "INSURANCE_EXPIRING", "Insurance expiring"
    REGISTRATION_EXPIRING = "REGISTRATION_EXPIRING", "Registration expiring"
    ROADWORTHINESS_EXPIRING = "ROADWORTHINESS_EXPIRING", "Road-worthiness expiring"
    GPS_OFFLINE = "GPS_OFFLINE", "GPS offline (no telemetry)"
    SYNC_FAILURE = "SYNC_FAILURE", "Telemetry sync failure"
    WEBHOOK_FAILURE = "WEBHOOK_FAILURE", "Webhook delivery failure"


class Severity(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class EntityType(models.TextChoices):
    RIDER = "rider", "Rider"
    ORDER = "order", "Order"
    MERCHANT = "merchant", "Merchant"
    VEHICLE = "vehicle", "Vehicle"
    ZONE = "zone", "Zone"
    SYSTEM = "system", "System"


class AlertStatus(models.TextChoices):
    NEW = "new", "New"
    INVESTIGATING = "investigating", "Investigating"
    RESOLVED = "resolved", "Resolved"
    FALSE_POSITIVE = "false_positive", "False Positive"


# Statuses that count as an "open" / active alert.
OPEN_ALERT_STATUSES = [AlertStatus.NEW, AlertStatus.INVESTIGATING]


class Alert(models.Model):
    """
    A single operational alert. The engine keeps **one open record per ongoing
    issue**, keyed by ``dedupe_key`` — it updates that row in place while the
    condition persists and auto-resolves it when the condition clears.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    alert_type = models.CharField(
        max_length=40, choices=AlertType.choices, db_index=True
    )
    severity = models.CharField(
        max_length=10, choices=Severity.choices, default=Severity.MEDIUM
    )
    entity_type = models.CharField(max_length=10, choices=EntityType.choices)

    # Nullable subject FKs — only the relevant one(s) are set per alert.
    rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ops_alerts",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ops_alerts",
    )
    merchant = models.ForeignKey(
        "dispatcher.Merchant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ops_alerts",
    )
    vehicle = models.ForeignKey(
        "dispatcher.VehicleAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ops_alerts",
    )
    zone = models.ForeignKey(
        "dispatcher.Zone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ops_alerts",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Measured number that tripped the rule (speed, hours, %, …)",
    )
    context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extra structured detail captured at fire time",
    )

    dedupe_key = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Stable key per ongoing issue, e.g. TYPE:<rider_id>:<date>",
    )

    status = models.CharField(
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.NEW,
        db_index=True,
    )
    resolution_note = models.TextField(blank=True, default="")
    resolved_at = models.DateTimeField(null=True, blank=True)

    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_alerts"
        ordering = ["-last_seen_at"]
        indexes = [
            models.Index(fields=["alert_type", "status"]),
            models.Index(fields=["severity", "-created_at"]),
            models.Index(fields=["status", "-last_seen_at"]),
            models.Index(fields=["dedupe_key"]),
        ]
        constraints = [
            # Enforce "one open record per ongoing issue" at the DB level.
            models.UniqueConstraint(
                fields=["dedupe_key"],
                condition=models.Q(status__in=["new", "investigating"]),
                name="uniq_open_alert_per_dedupe_key",
            ),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.alert_type} — {self.title} ({self.status})"

    @property
    def is_open(self):
        return self.status in OPEN_ALERT_STATUSES

    def resolve(self, note="", false_positive=False):
        """Mark this alert resolved (used by the engine and the resolve endpoint)."""
        self.status = (
            AlertStatus.FALSE_POSITIVE if false_positive else AlertStatus.RESOLVED
        )
        self.resolution_note = note
        self.resolved_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "resolution_note",
                "resolved_at",
                "updated_at",
            ]
        )


class AlertRule(models.Model):
    """
    Admin-editable configuration for one alert type — so the engine carries no
    hardcoded thresholds. Where a threshold already lives in
    ``dispatcher.SystemSettings`` (e.g. accept_timeout_sec, commission_pct),
    the rule reads it from there instead of duplicating it.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(
        max_length=40, choices=AlertType.choices, unique=True
    )
    is_enabled = models.BooleanField(default=True)

    default_severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.MEDIUM,
        help_text="Severity used when the rule has a single tier",
    )
    warn_threshold = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Numeric threshold for warning/high (rule-specific meaning)",
    )
    critical_threshold = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Numeric threshold for critical",
    )
    window_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time window the rule evaluates over (rule-specific)",
    )
    params = models.JSONField(
        default=dict,
        blank=True,
        help_text="Rule-specific config, e.g. {'curfew_hour': 20, 'vehicle_types': ['bike']}",
    )
    description = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_alert_rules"
        ordering = ["alert_type"]

    def __str__(self):
        state = "on" if self.is_enabled else "off"
        return f"AlertRule[{self.alert_type}] ({state})"


class FuelBill(models.Model):
    """
    One fuel-purchase row imported from the daily fuel bills spreadsheet
    (uploaded via /api/ops/fuel/upload/). Each spreadsheet row = one bill.

    `invoice_number` is the natural unique key, so re-uploading the same file
    updates rather than duplicates. `vehicle_plate` (the sheet's "Vehicle"
    column) links to `dispatcher.VehicleAsset` (and thus the rider) so fuel can
    be attributed per vehicle/rider. `bill_date` (derived from "Date") is the
    daily key the dashboard groups and filters on.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    branch = models.CharField(max_length=255, blank=True, default="")

    # "Vehicle" column = plate number; link to the fleet asset + rider.
    vehicle_plate = models.CharField(max_length=30, db_index=True)
    vehicle_asset = models.ForeignKey(
        "dispatcher.VehicleAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fuel_bills",
    )
    rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fuel_bills",
    )

    vehicle_brand = models.CharField(max_length=120, blank=True, default="")
    vehicle_model = models.CharField(max_length=120, blank=True, default="")
    internal_number = models.CharField(max_length=60, blank=True, default="")
    trip_number = models.CharField(max_length=60, blank=True, default="")
    fuel_type = models.CharField(max_length=60, blank=True, default="")

    fuel_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    worker_tip = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    km_per_l = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    l_per_100km = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    liters = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    odometer = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )

    payment_method = models.CharField(max_length=120, blank=True, default="")
    delegate = models.CharField(max_length=255, blank=True, default="")
    station = models.CharField(max_length=255, blank=True, default="")
    station_branch = models.CharField(max_length=255, blank=True, default="")
    location_text = models.CharField(max_length=255, blank=True, default="")
    station_location = models.CharField(max_length=120, blank=True, default="")

    bill_datetime = models.DateTimeField(null=True, blank=True)
    bill_date = models.DateField(db_index=True)

    raw = models.JSONField(
        default=dict, blank=True, help_text="Original spreadsheet row (audit)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_fuel_bills"
        ordering = ["-bill_datetime"]
        indexes = [
            models.Index(fields=["bill_date"]),
            models.Index(fields=["vehicle_plate", "bill_date"]),
            models.Index(fields=["rider", "bill_date"]),
        ]

    def __str__(self):
        return f"Fuel #{self.invoice_number} — {self.vehicle_plate} ₦{self.cost}"

