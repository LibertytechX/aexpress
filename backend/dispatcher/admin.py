from django.contrib import admin
from .models import Rider, DispatcherProfile, Merchant, SystemSettings, ActivityFeed, Zone, RelayNode, VehicleAsset


@admin.register(VehicleAsset)
class VehicleAssetAdmin(admin.ModelAdmin):
    list_display = (
        "asset_id",
        "plate_number",
        "vehicle_type",
        "make",
        "model",
        "engine_status",
        "is_active",
        "created_at",
    )
    list_filter = ("vehicle_type", "engine_status", "is_active")
    search_fields = ("asset_id", "plate_number", "vin", "make", "model")
    readonly_fields = ("id", "asset_id", "created_at", "updated_at")


@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "rider_id",
        "status",
        "vehicle_type",
        "vehicle_asset",
        "rating",
        "total_deliveries",
    )
    list_filter = ("status", "vehicle_type", "vehicle_asset__vehicle_type")
    search_fields = ("user__username", "user__email", "rider_id", "user__phone")
    autocomplete_fields = ("vehicle_asset",)


@admin.register(DispatcherProfile)
class DispatcherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username", "user__email", "user__phone")


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("user", "merchant_id", "created_at")
    search_fields = (
        "user__username",
        "user__email",
        "merchant_id",
        "user__business_name",
    )


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Prevent creating more than one settings object
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(ActivityFeed)
class ActivityFeedAdmin(admin.ModelAdmin):
    list_display = ("created_at", "event_type", "order_id", "text", "color")
    list_filter = ("event_type", "color")
    search_fields = ("order_id", "text")
    readonly_fields = ("id", "created_at")
    ordering = ("-created_at",)


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "center_lat", "center_lng", "radius_km", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")


class RelayNodeInline(admin.TabularInline):
    model = RelayNode
    extra = 0
    fields = ("name", "address", "latitude", "longitude", "catchment_radius_km", "is_active")


@admin.register(RelayNode)
class RelayNodeAdmin(admin.ModelAdmin):
    list_display = ("name", "zone", "latitude", "longitude", "catchment_radius_km", "is_active")
    list_filter = ("is_active", "zone")
    search_fields = ("name", "address")
    readonly_fields = ("id", "created_at", "updated_at")
