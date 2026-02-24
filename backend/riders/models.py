import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


class RiderAuth(models.Model):
    """
    Auth credentials for rider app login.
    Linked to dispatcher.Rider via OneToOne.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.OneToOneField(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="auth"
    )
    password_hash = models.CharField(max_length=255)
    pin = models.CharField(max_length=255, blank=True, default="")
    biometric_token = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Device-specific biometric auth token",
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    failed_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # OTP for phone verification / password reset
    otp_code = models.CharField(max_length=6, blank=True, default="")
    otp_expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rider_auth"

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    @property
    def is_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def record_failed_attempt(self):
        self.failed_attempts += 1
        if self.failed_attempts >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        self.save(update_fields=["failed_attempts", "locked_until"])

    def reset_failed_attempts(self):
        self.failed_attempts = 0
        self.locked_until = None
        self.save(update_fields=["failed_attempts", "locked_until"])


class RiderSession(models.Model):
    """
    JWT refresh token tracking.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="sessions"
    )
    refresh_token = models.CharField(max_length=500, unique=True, db_index=True)
    device_id = models.CharField(max_length=255, blank=True, default="")
    device_name = models.CharField(max_length=255, blank=True, default="")
    device_os = models.CharField(max_length=50, blank=True, default="")
    fcm_token = models.CharField(max_length=500, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "rider_sessions"
        ordering = ["-last_used_at"]


class RiderCodRecord(models.Model):
    """
    Tracks Cash On Delivery collections and remissions per rider.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Remission"
        REMITTED = "remitted", "Remitted"
        VERIFIED = "verified", "Verified"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="cod_records"
    )
    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="cod_records"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    remitted_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "rider_cod_records"
        ordering = ["-created_at"]


class RiderEarning(models.Model):
    """
    Per-trip earnings breakdown.
    """

    from decimal import Decimal

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="earnings"
    )
    order = models.OneToOneField(
        "orders.Order", on_delete=models.CASCADE, related_name="rider_earning"
    )
    base_fare = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    distance_fare = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    surge_bonus = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    tip = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    commission_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("20.00")
    )
    commission_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    net_earning = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    cod_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "rider_earnings"
        ordering = ["-created_at"]


class RiderDocument(models.Model):
    """
    KYC documents for riders.
    """

    class DocType(models.TextChoices):
        DRIVERS_LICENSE = "drivers_license", "Driver's License"
        VEHICLE_INSURANCE = "vehicle_insurance", "Vehicle Insurance"
        VEHICLE_REGISTRATION = "vehicle_registration", "Vehicle Registration"
        NATIONAL_ID = "national_id", "National ID"
        PROFILE_PHOTO = "profile_photo", "Profile Photo"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="documents"
    )
    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    file_url = models.URLField(max_length=500)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    expires_at = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rider_documents"
        ordering = ["-created_at"]


class OrderOffer(models.Model):
    """
    An order offered to a rider.
    """

    from decimal import Decimal

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="rider_offers"
    )
    rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.CASCADE,
        related_name="order_offers",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    estimated_earnings = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_offers"
        ordering = ["-created_at"]


class RiderDevice(models.Model):
    """
    Rider device tracking and permissions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="devices"
    )
    device_id = models.CharField(max_length=255, unique=True, db_index=True)
    fcm_token = models.CharField(max_length=500, blank=True, default="")
    platform = models.CharField(max_length=50, blank=True, default="")
    model_name = models.CharField(max_length=255, blank=True, default="")
    os_version = models.CharField(max_length=50, blank=True, default="")
    app_version = models.CharField(max_length=50, blank=True, default="")

    # Permissions tracking
    location_permission = models.CharField(
        max_length=50, blank=True, default="undetermined"
    )
    camera_permission = models.CharField(
        max_length=50, blank=True, default="undetermined"
    )
    notification_permission = models.CharField(
        max_length=50, blank=True, default="undetermined"
    )
    battery_optimization = models.CharField(
        max_length=50, blank=True, default="undetermined"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rider_devices"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Device {self.device_id} ({self.rider.rider_id})"


class AreaDemand(models.Model):
    """
    Real-time demand levels per area. Updated by Celery task.
    Shown on the Off-Duty screen.
    """

    class Level(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    area_name = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.LOW)
    pending_orders = models.IntegerField(default=0)
    active_riders = models.IntegerField(default=0)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "area_demand"
        ordering = ["area_name"]


class RiderNotification(models.Model):
    """
    Persisted notifications sent to riders.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "rider_notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.rider.rider_id}: {self.title}"
