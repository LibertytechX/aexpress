from django.contrib import admin
from .models import (
    Rider,
    DispatcherProfile,
    Merchant,
    SystemSettings,
    ActivityFeed,
    Zone,
    RelayNode,
    VehicleAsset,
    VehicleTracking,
    Vertical,
    ServiceAPIKey,
    VerticalLead,
    ZoneCaptain,
    RiderDutyLog,
    RiderDailySnapshot,
    MerchantDailySnapshot,
    DeliveryRating,
    ZoneTarget,
)


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


@admin.register(VehicleTracking)
class VehicleTrackingAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "vehicle_asset",
        "travelled",
        "unit_of_distance",
        "latitude",
        "longitude",
    )
    list_filter = ("unit_of_distance", "created_at")
    search_fields = (
        "vehicle_asset__asset_id",
        "vehicle_asset__plate_number",
        "vehicle_asset__provider_id",
    )
    autocomplete_fields = ("vehicle_asset",)
    readonly_fields = ("id", "created_at")
    ordering = ("-created_at",)


@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "rider_id",
        "status",
        "home_zone",
        "vehicle_type",
        "vehicle_asset",
        "rating",
        "total_deliveries",
    )
    list_filter = ("status", "home_zone", "vehicle_type", "vehicle_asset__vehicle_type")
    search_fields = ("user__username", "user__email", "rider_id", "user__phone")
    autocomplete_fields = ("vehicle_asset", "home_zone")
    actions = ["assign_zone"]

    @admin.action(description="Assign selected riders to a zone")
    def assign_zone(self, request, queryset):
        from django.shortcuts import render
        from django.http import HttpResponseRedirect
        from django import forms
        from django.contrib import messages
        from .models import Zone

        class AssignZoneForm(forms.Form):
            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            zone = forms.ModelChoiceField(
                queryset=Zone.objects.filter(is_active=True),
                required=True,
                label="Target Zone",
            )

        if "apply" in request.POST:
            form = AssignZoneForm(request.POST)
            if form.is_valid():
                zone = form.cleaned_data["zone"]
                updated_count = queryset.update(home_zone=zone)
                self.message_user(
                    request,
                    f"Successfully assigned {updated_count} riders to {zone.name}.",
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            from django.contrib.admin import helpers

            form = AssignZoneForm(
                initial={
                    "_selected_action": request.POST.getlist(
                        helpers.ACTION_CHECKBOX_NAME
                    )
                }
            )

        context = self.admin_site.each_context(request)
        context.update(
            {
                "form": form,
                "title": "Assign Zone to Riders",
                "queryset": queryset,
            }
        )
        return render(request, "admin/assign_zone_intermediate.html", context)


@admin.register(DispatcherProfile)
class DispatcherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username", "user__email", "user__phone")


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("user", "merchant_id", "zone", "activity_status", "created_at")
    list_filter = ("activity_status", "zone")
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


@admin.register(Vertical)
class VerticalAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "lead_name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code", "lead_name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "vertical",
        "center_lat",
        "center_lng",
        "radius_km",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "vertical")
    search_fields = ("name", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("vertical",)


class RelayNodeInline(admin.TabularInline):
    model = RelayNode
    extra = 0
    fields = (
        "name",
        "address",
        "latitude",
        "longitude",
        "catchment_radius_km",
        "is_active",
    )


@admin.register(RelayNode)
class RelayNodeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "zone",
        "latitude",
        "longitude",
        "catchment_radius_km",
        "is_active",
    )
    list_filter = ("is_active", "zone")
    search_fields = ("name", "address")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ServiceAPIKey)
class ServiceAPIKeyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "prefix",
        "is_active",
        "last_used_at",
        "expires_at",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "prefix")
    readonly_fields = ("id", "key_hash", "prefix", "created_at")


@admin.register(VerticalLead)
class VerticalLeadAdmin(admin.ModelAdmin):
    list_display = ("user", "vertical", "is_active", "created_at")
    list_filter = ("is_active",)


@admin.register(ZoneCaptain)
class ZoneCaptainAdmin(admin.ModelAdmin):
    list_display = ("user", "zone", "is_active", "created_at")
    list_filter = ("is_active",)


@admin.register(ZoneTarget)
class ZoneTargetAdmin(admin.ModelAdmin):
    list_display = ("zone", "month", "target_orders", "target_revenue")
    list_filter = ("month",)


@admin.register(DeliveryRating)
class DeliveryRatingAdmin(admin.ModelAdmin):
    list_display = ("rider", "score", "created_at")
    list_filter = ("score",)
    readonly_fields = ("id", "created_at")
