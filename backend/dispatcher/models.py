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
