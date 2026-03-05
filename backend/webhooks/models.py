from django.db import models
import uuid


class Webhook(models.Model):
    """
    Webhook model - Stores external dashboard configurations for outgoing webhooks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique name for the event (e.g., order-created)",
    )
    url = models.URLField(
        max_length=500, help_text="External URL to send the POST request to"
    )
    secret_key = models.CharField(
        max_length=255,
        help_text="Secret key used to generate HMAC-SHA256 signature for security",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "webhooks"
        ordering = ["event_name"]

    def __str__(self):
        return f"{self.event_name} -> {self.url}"


class WebhookOutbox(models.Model):
    """
    WebhookOutbox model - Records every outgoing webhook attempt for reliability and retries.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(
        Webhook, on_delete=models.CASCADE, related_name="deliveries"
    )
    payload = models.JSONField(help_text="The exact data sent in the webhook")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    retry_count = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "webhook_outbox"
        ordering = ["-created_at"]
        verbose_name_plural = "Webhook outbox records"

    def __str__(self):
        return f"{self.webhook.event_name} - {self.status} - Attempt {self.retry_count}"
