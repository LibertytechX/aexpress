from django.db import models
from django.conf import settings
import uuid
import random
import string


class Rider(models.Model):
    STATUS_CHOICES = (
        ("online", "Online"),
        ("on_delivery", "On Delivery"),
        ("offline", "Offline"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Auto-generated short ID
    rider_id = models.CharField(max_length=6, unique=True, db_index=True, blank=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rider_profile"
    )

    # Banking
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    bank_account_number = models.CharField(max_length=20, null=True, blank=True)
    bank_routing_code = models.CharField(max_length=20, null=True, blank=True)

    # Status & Settings
    WORKING_TYPE_CHOICES = (
        ("freelancer", "Freelancer"),
        ("full_time", "Full Time"),
    )
    working_type = models.CharField(
        max_length=20, choices=WORKING_TYPE_CHOICES, default="freelancer"
    )
    team = models.CharField(max_length=100, default="Main Team")
    is_authorized = models.BooleanField(
        default=False, help_text="Controls whether driver can receive jobs"
    )
    is_registration_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, help_text="Soft disable driver")

    # Vehicle Details (Expanded)
    vehicle_type = models.ForeignKey(
        "orders.Vehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="riders",
    )
    vehicle_model = models.CharField(max_length=100, default="Unknown")
    vehicle_plate_number = models.CharField(max_length=20, default="TEMP_PLATE")
    vehicle_color = models.CharField(max_length=50, null=True, blank=True)
    vehicle_photo = models.CharField(
        max_length=500, null=True, blank=True, help_text="S3 URL for vehicle photo"
    )

    # Status & Metrics
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="offline")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_deliveries = models.IntegerField(default=0)
    current_order = models.CharField(max_length=100, null=True, blank=True)

    # Contact & Location
    emergency_phone = models.CharField(max_length=20, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    avatar = models.CharField(
        max_length=500, null=True, blank=True, help_text="S3 URL for avatar"
    )
    last_seen_at = models.DateTimeField(null=True, blank=True)

    # Onro Fields
    onro_driver_id = models.CharField(
        max_length=100, null=True, blank=True, help_text="Driver ID from Onro"
    )
    onro_name = models.CharField(
        max_length=255, null=True, blank=True, help_text="Full name from Onro"
    )
    onro_language = models.CharField(
        max_length=10, default="en", help_text="Language preference"
    )
    onro_receive_email = models.BooleanField(
        default=True, help_text="Email notification preference"
    )
    onro_location_lat = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)
    onro_location_lng = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)

    # GPS Tracking
    gpswox_device_id = models.CharField(max_length=100, null=True, blank=True)
    current_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    current_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    current_speed = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_moving = models.BooleanField(default=False)
    last_location_update = models.DateTimeField(null=True, blank=True)

    # Documents
    driving_license_number = models.CharField(max_length=50, default="TEMP_LICENSE")
    national_id = models.CharField(max_length=50, default="TEMP_ID")
    driving_license_photo = models.CharField(max_length=500, null=True, blank=True, help_text="S3 URL for driving license")
    identity_card_photo = models.CharField(max_length=500, null=True, blank=True, help_text="S3 URL for ID card")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "riders"

    def save(self, *args, **kwargs):
        if not self.rider_id:
            # Generate unique 6-digit ID
            while True:
                new_id = "".join(random.choices(string.digits, k=6))
                if not Rider.objects.filter(rider_id=new_id).exists():
                    self.rider_id = new_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.contact_name or self.user.phone} ({self.rider_id})"


class DispatcherProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dispatcher_profile",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dispatcher_profiles"

    def __str__(self):
        return f"Dispatcher: {self.user.contact_name or self.user.phone}"


class Merchant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant_id = models.CharField(max_length=6, unique=True, db_index=True, blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="merchant_profile",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "merchants"

    def save(self, *args, **kwargs):
        if not self.merchant_id:
            # Generate unique 6-digit ID
            while True:
                new_id = "".join(random.choices(string.digits, k=6))
                if not Merchant.objects.filter(merchant_id=new_id).exists():
                    self.merchant_id = new_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.business_name} ({self.merchant_id})"


class SystemSettings(models.Model):
    """
    Singleton model to store global system settings/pricing configuration.
    """

    # Zone Surcharges
    bridge_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    outer_zone_surcharge = models.DecimalField(
        max_digits=10, decimal_places=2, default=800
    )
    island_premium = models.DecimalField(max_digits=10, decimal_places=2, default=300)

    # Weight Surcharges
    weight_threshold_kg = models.IntegerField(default=5)
    weight_surcharge_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, default=200
    )
    weight_unit_kg = models.IntegerField(default=5)

    # Surge Pricing
    surge_enabled = models.BooleanField(default=True)
    surge_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=1.5)
    surge_morning_start = models.TimeField(default="07:00")
    surge_morning_end = models.TimeField(default="09:30")
    surge_evening_start = models.TimeField(default="17:00")
    surge_evening_end = models.TimeField(default="20:00")
    rain_surge_enabled = models.BooleanField(default=True)
    rain_surge_multiplier = models.DecimalField(
        max_digits=3, decimal_places=1, default=1.3
    )

    # Tiered Pricing (Distance)
    tier_enabled = models.BooleanField(default=True)
    tier1_km = models.IntegerField(default=15)
    tier1_discount_pct = models.IntegerField(default=10)
    tier2_km = models.IntegerField(default=25)
    tier2_discount_pct = models.IntegerField(default=15)

    # Dispatch Rules
    auto_assign_enabled = models.BooleanField(default=True)
    auto_assign_radius_km = models.IntegerField(default=5)
    accept_timeout_sec = models.IntegerField(default=120)

    # Max Concurrent Orders
    max_concurrent_bike = models.IntegerField(default=2)
    max_concurrent_car = models.IntegerField(default=1)
    max_concurrent_van = models.IntegerField(default=1)

    # Fees
    cod_flat_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    cod_pct_fee = models.DecimalField(max_digits=4, decimal_places=2, default=1.5)

    # Notifications
    notif_new_order = models.BooleanField(default=True)
    notif_unassigned = models.BooleanField(default=True)
    notif_completed = models.BooleanField(default=True)
    notif_cod_settled = models.BooleanField(default=True)

    class Meta:
        db_table = "system_settings"
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def save(self, *args, **kwargs):
        # Singleton pattern enforcement
        if not self.pk and SystemSettings.objects.exists():
            return SystemSettings.objects.first()
        return super().save(*args, **kwargs)

    def __str__(self):
        return "Global Settings"


class ActivityFeed(models.Model):
    EVENT_TYPES = [
        ("new_order", "New Order"),
        ("assigned", "Assigned"),
        ("unassigned", "Unassigned"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
    ]
    COLOR_CHOICES = [
        ("gold", "Gold"),
        ("green", "Green"),
        ("red", "Red"),
        ("blue", "Blue"),
        ("purple", "Purple"),
        ("yellow", "Yellow"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    order_id = models.CharField(max_length=50, db_index=True)
    text = models.CharField(max_length=255)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default="gold")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "activity_feed"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.event_type}] {self.order_id} — {self.text[:50]}"
