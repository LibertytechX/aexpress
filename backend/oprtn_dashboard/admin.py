"""Admin registrations for the Operations Dashboard app."""

from django.contrib import admin

from .models import Alert, AlertRule, FuelBill


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = (
        "alert_type",
        "severity",
        "entity_type",
        "status",
        "title",
        "value",
        "last_seen_at",
    )
    list_filter = ("status", "severity", "alert_type", "entity_type")
    search_fields = ("title", "description", "dedupe_key")
    readonly_fields = (
        "dedupe_key",
        "first_seen_at",
        "last_seen_at",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = (
        "alert_type",
        "is_enabled",
        "default_severity",
        "warn_threshold",
        "critical_threshold",
        "window_minutes",
    )
    list_filter = ("is_enabled", "default_severity")
    search_fields = ("alert_type", "description")


@admin.register(FuelBill)
class FuelBillAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "bill_date",
        "vehicle_plate",
        "rider",
        "liters",
        "cost",
        "station",
    )
    list_filter = ("bill_date", "fuel_type", "payment_method")
    search_fields = ("invoice_number", "vehicle_plate", "station", "delegate")
    date_hierarchy = "bill_date"
    readonly_fields = ("created_at", "updated_at", "raw")
