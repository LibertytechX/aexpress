from django.contrib import admin
from django.utils import timezone

from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "rider",
        "category",
        "subject",
        "status",
        "priority",
        "whisper_sync_status",
        "created_at",
    )
    list_filter = ("status", "category", "priority", "whisper_sync_status")
    search_fields = (
        "reference",
        "subject",
        "rider__rider_id",
        "rider__user__phone",
        "order__order_number",
    )
    raw_id_fields = ("rider", "order")
    readonly_fields = (
        "reference",
        "rider",
        "order",
        "category",
        "subject",
        "message",
        "resolved_by",
        "resolved_at",
        "whisper_ticket_id",
        "whisper_sync_status",
        "whisper_sync_error",
        "whisper_synced_at",
        "created_at",
        "updated_at",
    )

    def get_readonly_fields(self, request, obj=None):
        # Whisper360 owns a synced ticket: ops work it on the Support desk, and
        # its status and reply flow back here. Editing them here would be overwritten.
        fields = super().get_readonly_fields(request, obj)
        if obj is not None and obj.whisper_ticket_id:
            return (*fields, "status", "priority", "resolution_note")
        return fields

    def save_model(self, request, obj, form, change):
        # Stamp who resolved the ticket and when
        if obj.status in (
            SupportTicket.Status.RESOLVED,
            SupportTicket.Status.CLOSED,
        ) and not obj.resolved_at:
            obj.resolved_at = timezone.now()
            obj.resolved_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False  # Tickets are lodged by riders via the API
