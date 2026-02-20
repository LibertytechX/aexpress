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


class RiderDevice(models.Model):
    """
    Device registration for push notifications.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="devices"
    )
    device_id = models.CharField(max_length=255, unique=True)
    fcm_token = models.CharField(max_length=500, blank=True, default="")
    platform = models.CharField(max_length=20, default="android")
    model_name = models.CharField(max_length=200, blank=True, default="")
    os_version = models.CharField(max_length=50, blank=True, default="")
    app_version = models.CharField(max_length=20, blank=True, default="")

    # Permission states (tracked for support/debugging)
    location_permission = models.CharField(
        max_length=30, default="not_asked"
    )  # granted/denied/not_asked
    camera_permission = models.CharField(max_length=30, default="not_asked")
    notification_permission = models.CharField(max_length=30, default="not_asked")
    battery_optimization = models.CharField(max_length=30, default="not_asked")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rider_devices"
