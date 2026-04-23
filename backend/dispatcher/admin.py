from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields

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
    MerchantDevice,
    MerchantNotification,
    MerchantNotificationSettings,
    VehicleReassignment,
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

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class RiderResource(resources.ModelResource):
    rider_name = fields.Field(column_name="Rider Name")
    yesterday_completed_order_count = fields.Field(
        column_name="Yesterday Completed Orders"
    )
    total_amount_for_previous_day = fields.Field(
        column_name="Previous Day Total Amount"
    )
    yesterday_distance = fields.Field(column_name="Previous Day Distance (km)")
    completed_today = fields.Field(column_name="Completed Today")
    completed_this_week = fields.Field(column_name="Completed This Week")
    completed_this_month = fields.Field(column_name="Completed This Month")
    overall_completed = fields.Field(column_name="Overall Completed")
    distance_all_time = fields.Field(column_name="Distance All Time (km)")

    class Meta:
        model = Rider
        fields = (
            "rider_id",
            "status",
            "rating",
            "total_deliveries",
            "is_active",
            "rider_name",
            "yesterday_completed_order_count",
            "total_amount_for_previous_day",
            "yesterday_distance",
            "completed_today",
            "completed_this_week",
            "completed_this_month",
            "overall_completed",
            "distance_all_time",
        )
        export_order = fields

    def dehydrate_rider_name(self, rider):
        return rider.user.get_full_name()

    def dehydrate_yesterday_completed_order_count(self, rider):
        if hasattr(rider, "yesterday_completed_order_count_annotated"):
            return rider.yesterday_completed_order_count_annotated
        else:
            from django.utils import timezone
            from datetime import timedelta
            from orders.models import Order

            yesterday = timezone.now().date() - timedelta(days=1)
            return Order.objects.filter(
                rider=rider, status="Done", completed_at__date=yesterday
            ).count()

    def dehydrate_total_amount_for_previous_day(self, rider):
        if hasattr(rider, "total_amount_for_previous_day_annotated"):
            val = rider.total_amount_for_previous_day_annotated
        else:
            from django.utils import timezone
            from datetime import timedelta
            from orders.models import Order
            from django.db.models import Sum

            yesterday = timezone.now().date() - timedelta(days=1)
            val = Order.objects.filter(
                rider=rider, status="Done", completed_at__date=yesterday
            ).aggregate(total=Sum("total_amount"))["total"]
        return round(val, 2) if val else 0.00

    def dehydrate_yesterday_order_distance(self, rider):
        val = getattr(rider, "total_yesterday_order_distance_annotated", 0)
        return round(val, 2) if val else 0.00

    def dehydrate_yesterday_distance(self, rider):
        return rider.yesterday_distance_covered()

    def dehydrate_distance_all_time(self, rider):
        val = getattr(rider, "all_time_distance_annotated", 0)
        return round(val, 2) if val else 0.00

    def dehydrate_completed_today(self, rider):
        return getattr(rider, "today_completed_count_annotated", 0)

    def dehydrate_completed_this_week(self, rider):
        return getattr(rider, "week_completed_count_annotated", 0)

    def dehydrate_completed_this_month(self, rider):
        return getattr(rider, "month_completed_count_annotated", 0)

    def dehydrate_overall_completed(self, rider):
        return getattr(rider, "total_completed_count_annotated", 0)

    def get_queryset(self):
        qs = super().get_queryset()
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Sum, Q

        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        qs = qs.annotate(
            yesterday_completed_order_count_annotated=Count(
                "rider_orders",
                filter=Q(
                    rider_orders__status="Done",
                    rider_orders__completed_at__date=yesterday,
                ),
                distinct=True,
            ),
            total_amount_for_previous_day_annotated=Sum(
                "rider_orders__total_amount",
                filter=Q(
                    rider_orders__status="Done",
                    rider_orders__completed_at__date=yesterday,
                ),
            ),
            total_yesterday_order_distance_annotated=Sum(
                "rider_orders__distance_km",
                filter=Q(rider_orders__created_at__date=yesterday),
            ),
            today_completed_count_annotated=Count(
                "rider_orders",
                filter=Q(
                    rider_orders__status="Done",
                    rider_orders__completed_at__date=today,
                ),
                distinct=True,
            ),
            week_completed_count_annotated=Count(
                "rider_orders",
                filter=Q(
                    rider_orders__status="Done",
                    rider_orders__completed_at__date__gte=week_start,
                ),
                distinct=True,
            ),
            month_completed_count_annotated=Count(
                "rider_orders",
                filter=Q(
                    rider_orders__status="Done",
                    rider_orders__completed_at__date__gte=month_start,
                ),
                distinct=True,
            ),
            total_completed_count_annotated=Count(
                "rider_orders",
                filter=Q(rider_orders__status="Done"),
                distinct=True,
            ),
            all_time_distance_annotated=Sum(
                "rider_orders__distance_km",
                filter=Q(rider_orders__status="Done"),
            ),
        )
        return qs


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


@admin.register(VehicleReassignment)
class VehicleReassignmentAdmin(admin.ModelAdmin):
    list_display = ("created_at", "vehicle_asset", "from_rider", "to_rider", "admin")
    list_filter = ("created_at", "admin")
    search_fields = (
        "from_rider__rider_id",
        "to_rider__rider_id",
        "vehicle_asset__plate_number",
        "admin__username",
    )
    readonly_fields = (
        "id",
        "from_rider",
        "to_rider",
        "vehicle_asset",
        "admin",
        "created_at",
    )
    ordering = ("-created_at",)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


@admin.register(Rider)
class RiderAdmin(ImportExportModelAdmin):
    resource_class = RiderResource
    list_display = (
        "rider_name",
        "rider_id",
        "status",
        "hub",
        "vehicle_type",
        "vehicle_asset",
        "rating",
        "total_deliveries",
        "is_active",
        "is_deleted",
        "completed_today",
        "is_jumia_rider",
        "completed_this_week",
        "completed_this_month",
        "overall_completed",
        "distance_all_time",
        "yesterday_completed_order_count",
    )
    list_filter = (
        "status",
        "hub__zone",
        "vehicle_type",
        "vehicle_asset__vehicle_type",
        "is_jumia_rider",
        "is_active",
        "is_deleted",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "rider_id",
        "user__phone",
    )
    autocomplete_fields = ("vehicle_asset", "hub")
    actions = ["assign_zone", "soft_delete_riders", "mark_as_jumia_riders"]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    @admin.action(description="Soft delete selected riders")
    def soft_delete_riders(self, request, queryset):
        from django.contrib import messages

        updated_count = queryset.update(is_deleted=True, is_active=False)
        self.message_user(
            request,
            f"Successfully soft deleted {updated_count} riders.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Mark selected riders as jumia riders")
    def mark_as_jumia_riders(self, request, queryset):
        from django.contrib import messages

        updated_count = queryset.update(is_jumia_rider=True)
        self.message_user(
            request,
            f"Successfully marked {updated_count} riders as jumia riders.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Assign selected riders to a hub")
    def assign_zone(self, request, queryset):
        from django.shortcuts import render
        from django.http import HttpResponseRedirect
        from django import forms
        from django.contrib import messages
        from .models import RelayNode

        class AssignHubForm(forms.Form):
            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            hub = forms.ModelChoiceField(
                queryset=RelayNode.objects.filter(is_active=True),
                required=True,
                label="Target Hub",
            )

        if "apply" in request.POST:
            form = AssignHubForm(request.POST)
            if form.is_valid():
                hub = form.cleaned_data["hub"]
                updated_count = queryset.update(hub=hub)
                self.message_user(
                    request,
                    f"Successfully assigned {updated_count} riders to {hub.name}.",
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            from django.contrib.admin import helpers

            form = AssignHubForm(
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
                "title": "Assign Hub to Riders",
                "queryset": queryset,
            }
        )
        return render(request, "admin/assign_zone_intermediate.html", context)

    def get_queryset(self, request):
        qs = Rider.objects.all_with_deleted()
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Sum, Q

        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        qs = qs.annotate(
            yesterday_completed_order_count_annotated=Count(
                "rider_orders",
                filter=Q(
                    rider_orders__status="Done",
                    rider_orders__completed_at__date=yesterday,
                ),
                distinct=True,
            ),
            total_amount_for_previous_day_annotated=Sum(
                "rider_orders__total_amount",
                filter=Q(
                    rider_orders__status="Done",
                    rider_orders__completed_at__date=yesterday,
                ),
            ),
            total_yesterday_order_distance_annotated=Sum(
                "rider_orders__distance_km",
                filter=Q(rider_orders__created_at__date=yesterday),
            ),
            today_completed_count_annotated=Count(
                "rider_orders",
                filter=Q(
                    rider_orders__status="Done",
                    rider_orders__completed_at__date=today,
                ),
                distinct=True,
            ),
            week_completed_count_annotated=Count(
                "rider_orders",
                filter=Q(
                    rider_orders__status="Done",
                    rider_orders__completed_at__date__gte=week_start,
                ),
                distinct=True,
            ),
            month_completed_count_annotated=Count(
                "rider_orders",
                filter=Q(
                    rider_orders__status="Done",
                    rider_orders__completed_at__date__gte=month_start,
                ),
                distinct=True,
            ),
            total_completed_count_annotated=Count(
                "rider_orders",
                filter=Q(rider_orders__status="Done"),
                distinct=True,
            ),
            all_time_distance_annotated=Sum(
                "rider_orders__distance_km",
                filter=Q(rider_orders__status="Done"),
            ),
        )
        return qs

    @admin.display(description="Rider Name", ordering="user__first_name")
    def rider_name(self, obj):
        return obj.user.get_full_name()

    @admin.display(
        description="Today Orders",
        ordering="today_completed_count_annotated",
    )
    def completed_today(self, obj):
        return getattr(obj, "today_completed_count_annotated", 0)

    @admin.display(
        description="This Week Orders",
        ordering="week_completed_count_annotated",
    )
    def completed_this_week(self, obj):
        return getattr(obj, "week_completed_count_annotated", 0)

    @admin.display(
        description="This Month Orders",
        ordering="month_completed_count_annotated",
    )
    def completed_this_month(self, obj):
        return getattr(obj, "month_completed_count_annotated", 0)

    @admin.display(
        description="Overall Orders",
        ordering="total_completed_count_annotated",
    )
    def overall_completed(self, obj):
        return getattr(obj, "total_completed_count_annotated", 0)

    @admin.display(
        description="Distance All Time (km)",
        ordering="all_time_distance_annotated",
    )
    def distance_all_time(self, obj):
        val = getattr(obj, "all_time_distance_annotated", 0)
        return round(val, 2) if val else 0.00

    @admin.display(
        description="Yesterday Completed Orders",
        ordering="yesterday_completed_order_count_annotated",
    )
    def yesterday_completed_order_count(self, obj):
        return getattr(obj, "yesterday_completed_order_count_annotated", 0)

    @admin.display(
        description="Prev Day Total Amount",
        ordering="total_amount_for_previous_day_annotated",
    )
    def total_amount_for_previous_day(self, obj):
        val = getattr(obj, "total_amount_for_previous_day_annotated", 0)
        return round(val, 2) if val else 0.00

    # @admin.display(description="Prev Day Distance (km)")
    # def yesterday_distance(self, obj):
    #     return obj.yesterday_distance_covered()

    @admin.display(
        description="Prev Day Orders (km)",
        ordering="total_yesterday_order_distance_annotated",
    )
    def yesterday_order_distance(self, obj):
        val = getattr(obj, "total_yesterday_order_distance_annotated", 0)
        return round(val, 2) if val else 0.00


@admin.register(DispatcherProfile)
class DispatcherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__phone",
    )


class MerchantResource(resources.ModelResource):
    name = fields.Field(column_name="Name")
    email = fields.Field(attribute="user__email", column_name="Email")
    phone = fields.Field(attribute="user__phone", column_name="Phone")
    last_login = fields.Field(attribute="user__last_login", column_name="Last Login")

    class Meta:
        model = Merchant
        fields = (
            "name",
            "email",
            "phone",
            "last_login",
            "merchant_id",
            "activity_status",
            "acquisition_source",
            "merchant_type",
            "created_at",
        )
        export_order = (
            "name",
            "email",
            "phone",
            "merchant_id",
            "activity_status",
            "acquisition_source",
            "created_at",
            "last_login",
        )

    def dehydrate_name(self, merchant):
        return merchant.user.get_full_name()


@admin.register(Merchant)
class MerchantAdmin(ImportExportModelAdmin):
    resource_class = MerchantResource
    list_display = (
        "get_name",
        "get_email",
        "get_phone",
        "merchant_id",
        "activity_status",
        "acquisition_source",
        "merchant_type",
        "created_at",
        "is_partner",
        "get_last_login",
        "can_group_orders",
    )
    list_filter = ("activity_status", "zone", "acquisition_source", "is_partner")
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__phone",
        "merchant_id",
        "user__business_name",
    )

    @admin.display(description="Name", ordering="user__first_name")
    def get_name(self, obj):
        return obj.user.get_full_name()

    @admin.display(description="Email", ordering="user__email")
    def get_email(self, obj):
        return obj.user.email

    @admin.display(description="Phone Number", ordering="user__phone")
    def get_phone(self, obj):
        return obj.user.phone

    @admin.display(description="Last Login", ordering="user__last_login")
    def get_last_login(self, obj):
        return obj.user.last_login


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
    actions = ["set_active", "set_inactive"]

    @admin.action(description="Set selected zones as active")
    def set_active(self, request, queryset):
        from django.contrib import messages

        updated_count = queryset.update(is_active=True)
        self.message_user(
            request,
            f"Successfully marked {updated_count} zones as active.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Set selected zones as inactive")
    def set_inactive(self, request, queryset):
        from django.contrib import messages

        updated_count = queryset.update(is_active=False)
        self.message_user(
            request,
            f"Successfully marked {updated_count} zones as inactive.",
            level=messages.SUCCESS,
        )


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
    ordering = ("-created_at",)


@admin.register(MerchantDevice)
class MerchantDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "merchant",
        "device_id",
        "platform",
        "model_name",
        "is_active",
        "created_at",
    )
    list_filter = ("platform", "is_active", "created_at")
    search_fields = ("merchant__merchant_id", "device_id", "fcm_token")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(MerchantNotification)
class MerchantNotificationAdmin(admin.ModelAdmin):
    list_display = ("merchant", "title", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("merchant__merchant_id", "title", "body")
    readonly_fields = ("id", "created_at")


@admin.register(MerchantNotificationSettings)
class MerchantNotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ("merchant", "push_enabled", "updated_at")
    list_filter = ("push_enabled",)
    search_fields = ("merchant__merchant_id",)
    readonly_fields = ("id", "created_at", "updated_at")
