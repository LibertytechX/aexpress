import secrets
import uuid

from django.conf import settings
from django.db import models


def generate_ticket_reference():
    """Short, human-friendly reference riders can quote to support, e.g. TCK-8F3A2C."""
    return f"TCK-{secrets.token_hex(3).upper()}"


class SupportTicket(models.Model):
    """
    A complaint or support request lodged by a rider.
    Pushed to Whisper360's Support desk, where the ops team works it; status and
    the team's reply come back from there (see support/whisper360.py).
    """

    class Category(models.TextChoices):
        PAYMENT = "payment", "Payment / Earnings"
        ORDER = "order", "Order / Delivery"
        TECHNICAL = "technical", "App / Technical"
        SAFETY = "safety", "Safety / Incident"
        ACCOUNT = "account", "Account"
        GENERAL = "general", "General"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class WhisperSync(models.TextChoices):
        PENDING = "pending", "Pending"
        SYNCED = "synced", "Synced"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(
        max_length=20, unique=True, db_index=True, default=generate_ticket_reference
    )
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="support_tickets"
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
    )
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.GENERAL
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )

    # Filled in by the ops team when the ticket is handled
    resolution_note = models.TextField(blank=True, default="")
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_support_tickets",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Whisper360 Support desk link. Once synced, Whisper360 owns status and the
    # resolution note; ops no longer edit them here.
    whisper_ticket_id = models.UUIDField(null=True, blank=True, unique=True)
    whisper_sync_status = models.CharField(
        max_length=10,
        choices=WhisperSync.choices,
        default=WhisperSync.PENDING,
        db_index=True,
    )
    whisper_sync_error = models.CharField(max_length=300, blank=True, default="")
    whisper_synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "support_tickets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} — {self.subject[:40]}"
