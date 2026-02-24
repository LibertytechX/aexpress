from django.contrib import admin
from .models import (
    RiderAuth,
    RiderSession,
    RiderCodRecord,
    RiderEarning,
    RiderDocument,
    OrderOffer,
    RiderDevice,
    AreaDemand,
)


@admin.register(AreaDemand)
class AreaDemandAdmin(admin.ModelAdmin):
    list_display = (
        "area_name",
        "level",
        "pending_orders",
        "active_riders",
        "updated_at",
    )
    list_filter = ("level",)
    search_fields = ("area_name",)


@admin.register(RiderAuth)
class RiderAuthAdmin(admin.ModelAdmin):
    list_display = ("rider", "is_active", "is_verified", "created_at")


@admin.register(RiderSession)
class RiderSessionAdmin(admin.ModelAdmin):
    list_display = ("rider", "device_id", "is_active", "last_used_at")


@admin.register(RiderCodRecord)
class RiderCodRecordAdmin(admin.ModelAdmin):
    list_display = ("rider", "order", "amount", "status", "created_at")


@admin.register(RiderEarning)
class RiderEarningAdmin(admin.ModelAdmin):
    list_display = ("rider", "order", "net_earning", "created_at")


@admin.register(RiderDocument)
class RiderDocumentAdmin(admin.ModelAdmin):
    list_display = ("rider", "doc_type", "status", "created_at")


@admin.register(OrderOffer)
class OrderOfferAdmin(admin.ModelAdmin):
    list_display = ("order", "rider", "status", "created_at")


@admin.register(RiderDevice)
class RiderDeviceAdmin(admin.ModelAdmin):
    list_display = ("rider", "device_id", "platform", "is_active")
