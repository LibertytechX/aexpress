from django.db import models
from django.conf import settings


class WhatsAppMessage(models.Model):
    """Log of every outbound WhatsApp message sent via 360Messenger."""

    class EventType(models.TextChoices):
        SIGNUP = "signup", "User Signup"
        ONBOARDING = "onboarding", "Onboarding Complete"
        ORDER_CREATED = "order_created", "Order Created"
        RIDER_ASSIGNED = "rider_assigned", "Rider Assigned"
        ORDER_PICKED_UP = "order_picked_up", "Order Picked Up"
        ORDER_DELIVERED = "order_delivered", "Order Delivered"
        ORDER_CANCELLED = "order_cancelled", "Order Cancelled"
        RELAY_LEG_ASSIGNED = "relay_leg_assigned", "Relay Leg Assigned"
        DISPATCHER_ONBOARDED = "dispatcher_onboarded", "Dispatcher Onboarded"
        REFERRAL_COMMISSION = "referral_commission", "Referral Commission"
        DRIP_CAMPAIGN = "drip_campaign", "Drip Campaign"
        WEEKLY_REPORT = "weekly_report", "Weekly Report"
        RIDER_ORDER_OFFER = "rider_order_offer", "Rider Order Offer"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"

    recipient_phone = models.CharField(max_length=20, db_index=True)
    event_type = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    message_content = models.TextField()
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.PENDING
    )
    external_message_id = models.CharField(
        max_length=100, blank=True, default=""
    )
    error_message = models.TextField(blank=True, default="")
    related_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whatsapp_messages",
    )
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whatsapp_messages",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "WhatsApp Message"
        verbose_name_plural = "WhatsApp Messages"

    def __str__(self):
        return f"[{self.event_type}] → {self.recipient_phone} ({self.status})"
