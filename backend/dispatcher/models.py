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

    # Vehicle Details (consolidated)
    vehicle_type = models.ForeignKey(
        "orders.Vehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="riders",
    )
    # Status & Metrics
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="offline")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    total_deliveries = models.IntegerField(default=0)
    current_order = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dispatcher_profile",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def save(self, *args, **kwargs):
        # Singleton pattern enforcement
        if not self.pk and SystemSettings.objects.exists():
            return SystemSettings.objects.first()
        return super().save(*args, **kwargs)

    def __str__(self):
        return "Global Settings"
