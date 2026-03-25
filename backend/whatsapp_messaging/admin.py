from django.contrib import admin
from .models import WhatsAppMessage


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = [
        "recipient_phone", "event_type", "status",
        "external_message_id", "created_at", "sent_at",
    ]
    list_filter = ["event_type", "status", "created_at"]
    search_fields = ["recipient_phone", "message_content", "external_message_id"]
    readonly_fields = [
        "recipient_phone", "event_type", "message_content", "status",
        "external_message_id", "error_message", "related_order",
        "related_user", "created_at", "sent_at",
    ]
    ordering = ["-created_at"]
