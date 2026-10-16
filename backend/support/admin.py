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
        "created_at",
    )
    list_filter = ("status", "category", "priority")
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
        "created_at",
        "updated_at",
    )

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
