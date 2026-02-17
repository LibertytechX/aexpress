import uuid
from django.db import models
from django.utils import timezone
from authentication.models import User


class Vehicle(models.Model):
    """Vehicle types available for delivery."""

    name = models.CharField(max_length=50, unique=True)
    max_weight_kg = models.IntegerField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "vehicles"
        ordering = ["base_price"]

    def __str__(self):
        return f"{self.name} - ₦{self.base_price}"


class Order(models.Model):
    """Main order model for delivery requests."""

    MODE_CHOICES = [
        ("quick", "Quick Send"),
        ("multi", "Multi-Drop"),
        ("bulk", "Bulk Import"),
    ]

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Assigned", "Assigned"),
        ("Started", "Started"),
        ("Done", "Done"),
        ("CustomerCanceled", "Customer Canceled"),
        ("RiderCanceled", "Rider Canceled"),
        ("Failed", "Failed"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("wallet", "Wallet"),
        ("cash_on_pickup", "Cash on Pickup"),
        ("receiver_pays", "Receiver Pays"),
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
    sender_name = models.CharField(max_length=255)
    sender_phone = models.CharField(max_length=20)

    # Payment
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default="wallet"
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

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
    scheduled_pickup_time = models.DateTimeField(null=True, blank=True)

    # Additional info
    notes = models.TextField(blank=True)

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

    # Dropoff information
    dropoff_address = models.TextField()
    receiver_name = models.CharField(max_length=255)
    receiver_phone = models.CharField(max_length=20)

    # Package details
    package_type = models.CharField(
        max_length=20, choices=PACKAGE_TYPE_CHOICES, default="Box"
    )
    notes = models.TextField(blank=True)

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
