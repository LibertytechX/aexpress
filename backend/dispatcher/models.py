from django.db import models
from django.conf import settings
import uuid


class Vehicle(models.Model):
    VEHICLE_TYPES = (
        ("Bike", "Bike"),
        ("Car", "Car"),
        ("Van", "Van"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(
        max_length=20, choices=[(x, x) for x in ["Bike", "Car", "Van"]]
    )
    plate_number = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type} - {self.plate_number}"


class Rider(models.Model):
    STATUS_CHOICES = (
        ("online", "Online"),
        ("on_delivery", "On Delivery"),
        ("offline", "Offline"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rider_profile"
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="riders"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="offline")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    total_deliveries = models.IntegerField(default=0)
    current_order = models.CharField(
        max_length=100, null=True, blank=True
    )  # Placeholder for now, link to Order model later

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.user.phone)
