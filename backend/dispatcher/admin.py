from django.contrib import admin
from .models import Rider, DispatcherProfile, Merchant, SystemSettings


@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "rider_id",
        "status",
        "vehicle_type",
        "rating",
        "total_deliveries",
    )
    list_filter = ("status", "vehicle_type")
    search_fields = ("user__username", "user__email", "rider_id", "user__phone")


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
