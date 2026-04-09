import logging
from decimal import Decimal

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum

from dispatcher.models import SystemSettings
from dispatcher.tasks import send_merchant_notification
from riders.models import RiderEarning, RiderCodRecord
from riders.notifications import notify_rider
from wallet.models import Wallet

from .models import Vehicle, Order, Delivery, OrderLeg, MerchantPricingOverride, MerchantPriceList, MerchantPriceListItem

logger = logging.getLogger(__name__)

_COD_METHODS = {"cash", "cash_on_pickup", "receiver_pays"}
_DEFAULT_COMMISSION_PCT = Decimal("20.00")


def complete_order_for_rider(modeladmin, request, queryset):
    """
    Admin action: force-complete selected orders for their assigned rider.

    Mirrors OrderCompleteView but skips the proximity check. The order must
    already have an assigned rider. Steps:
      1. COD wallet balance check & debit (for cash-based orders).
      2. Calculate commission, create RiderEarning, credit rider wallet.
      3. Mark pending RiderCodRecord as remitted.
      4. Mark all deliveries Delivered, advance order status to Done.
      5. Send push notification to the rider.
    """
    completed = 0
    skipped = []

    for order in queryset.select_related("rider", "rider__user"):
        order_number = order.order_number

        # ── Guard: must have an assigned rider ────────────────────────────────
        rider = order.rider
        if not rider:
            skipped.append(f"{order_number} (no rider assigned)")
            continue

        # ── Guard: order must not already be Done ─────────────────────────────
        if order.status == "Done":
            skipped.append(f"{order_number} (already Done)")
            continue

        try:
            # ── Step 1: COD wallet balance check ──────────────────────────────
            # is_cod = order.payment_method in _COD_METHODS
            cod_total = Decimal("0.00")

            # ── Step 2: Calculate and record rider earnings ────────────────────
            settings_obj = SystemSettings.objects.first()
            commission_pct = (
                settings_obj.commission_pct if settings_obj else _DEFAULT_COMMISSION_PCT
            )

            order_amount = Decimal(str(order.total_amount))
            commission_amount = (commission_pct / Decimal("100")) * order_amount
            # net_earning = commission_amount

            RiderEarning.objects.get_or_create(
                order=order,
                defaults={
                    "rider": rider,
                    "base_fare": order_amount,
                    "commission_pct": commission_pct,
                    "commission_amount": commission_amount,
                    "net_earning": commission_amount,
                    "cod_amount": cod_total,
                },
            )

            # ── Step 4: Mark all deliveries Delivered, advance order to Done ──
            for d in order.deliveries.exclude(status="Delivered"):
                d.status = "Delivered"
                d.delivered_at = timezone.now()
                d.save(update_fields=["status", "delivered_at"])

            order.status = "Done"
            if not order.completed_at:
                order.completed_at = timezone.now()
            order.save(update_fields=["status", "completed_at", "updated_at"])

            # ── Step 5: Push notification ─────────────────────────────────────
            try:
                notify_rider(
                    rider=rider,
                    title="Order Completed 🎉",
                    body=(
                        f"Order #{order_number} completed. "
                        # f"₦{net_earning} credited to your wallet."
                    ),
                    data={
                        "order_number": order_number,
                        # "net_earning": str(net_earning),
                    },
                )
            except Exception as exc:
                logger.warning(
                    "Failed to send completion notification to rider %s: %s",
                    rider.rider_id,
                    exc,
                )

            # Notify the merchant that their order was delivered
            try:
                merchant_profile = getattr(order.merchant, "merchant_profile", None)
                if merchant_profile:
                    send_merchant_notification.delay(
                        merchant_id=str(merchant_profile.id),
                        title="Order Delivered ✅",
                        body=f"Your order #{order_number} has been delivered successfully.",
                        data={"order_number": order_number, "status": "Done"},
                        category="order_completed",
                    )
            except Exception as exc:
                logger.warning(
                    "Merchant completion notification failed for order %s: %s",
                    order_number,
                    exc,
                )

            completed += 1
            logger.info(
                "Admin action: order %s completed for rider %s by %s",
                order_number,
                rider.rider_id,
                request.user,
            )

        except Exception as exc:
            logger.error(
                "Admin action: failed to complete order %s — %s", order_number, exc
            )
            skipped.append(f"{order_number} (unexpected error: {exc})")

    if completed:
        modeladmin.message_user(
            request,
            f"Successfully completed {completed} order(s).",
        )
    if skipped:
        modeladmin.message_user(
            request,
            f"Skipped {len(skipped)} order(s): {', '.join(skipped)}",
            level="warning",
        )


complete_order_for_rider.short_description = (
    "Complete order for assigned rider (no proximity check)"
)


class AssignedRiderFilter(admin.SimpleListFilter):
    title = _("assigned rider")
    parameter_name = "has_rider"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(rider__isnull=False)
        if self.value() == "no":
            return queryset.filter(rider__isnull=True)
        return queryset


class DeliveryInline(admin.TabularInline):
    """Inline admin for deliveries within an order."""

    model = Delivery
    extra = 0
    fields = [
        "sequence",
        "pickup_address",
        "sender_name",
        "sender_phone",
        "dropoff_address",
        "dropoff_latitude",
        "dropoff_longitude",
        "receiver_name",
        "receiver_phone",
        "package_type",
        "status",
    ]
    readonly_fields = ["sequence"]


class OrderLegInline(admin.TabularInline):
    """Inline admin for relay legs within an order."""

    model = OrderLeg
    extra = 0
    fields = [
        "leg_number",
        "status",
        "rider",
        "start_relay_node",
        "end_relay_node",
        "distance_km",
        "rider_payout",
        "hub_pin",
    ]
    readonly_fields = ["leg_number", "hub_pin"]


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Admin configuration for Vehicle model."""

    list_display = ["name", "max_weight_kg", "base_price", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    ordering = ["base_price"]


@admin.register(MerchantPricingOverride)
class MerchantPricingOverrideAdmin(admin.ModelAdmin):
    list_display = [
        "merchant",
        "vehicle",
        "is_active",
        "flat_fee",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_active", "vehicle", "created_at"]
    search_fields = ["merchant__id", "merchant__business_name", "merchant__phone"]
    ordering = ["-created_at"]


class MerchantPriceListItemInline(admin.TabularInline):
    model = MerchantPriceListItem
    extra = 1


@admin.register(MerchantPriceList)
class MerchantPriceListAdmin(admin.ModelAdmin):
    list_display = ["name", "merchant", "vehicle", "is_active", "created_at"]
    list_filter = ["is_active", "vehicle", "created_at"]
    search_fields = ["name", "merchant__business_name", "merchant__phone"]
    inlines = [MerchantPriceListItemInline]
    ordering = ["-created_at"]


class MerchantPriceListItemResource(resources.ModelResource):
    class Meta:
        model = MerchantPriceListItem
        fields = ("id", "price_list", "label", "min_km", "max_km", "fixed_fee")
        export_order = fields


@admin.register(MerchantPriceListItem)
class MerchantPriceListItemAdmin(ImportExportModelAdmin):
    resource_class = MerchantPriceListItemResource
    list_display = ["label", "price_list", "min_km", "max_km", "fixed_fee"]
    list_filter = ["price_list"]
    search_fields = ["label", "price_list__name"]
    ordering = ["min_km"]


class OrderResource(resources.ModelResource):
    user_name_display = fields.Field(column_name="User Name")
    rider_name_display = fields.Field(column_name="Rider Name")
    rider_id_display = fields.Field(column_name="Rider ID")
    vehicle_asset_id_display = fields.Field(column_name="Vehicle Asset ID")
    collect_on_delivery_for_merchant = fields.Field(
        column_name="Collect On Delivery For Merchant"
    )
    rider_earning = fields.Field(column_name="Rider Earning")

    class Meta:
        model = Order
        fields = (
            "order_number",
            "user_name_display",
            "rider_name_display",
            "rider_id_display",
            "mode",
            "is_relay_order",
            "vehicle",
            "vehicle_asset_id_display",
            "status",
            "payment_status",
            "payment_method",
            "total_amount",
            "distance_km",
            "duration_minutes",
            "assigned_at",
            "picked_up_at",
            "arrived_at",
            "completed_at",
            "collect_on_delivery_for_merchant",
            "cod_amount",
            "rider_earning",
            "created_at",
        )
        export_order = fields

    def dehydrate_user_name_display(self, obj):
        return obj.user.get_full_name() if obj.user else "-"

    def dehydrate_collect_on_delivery_for_merchant(self, obj):
        return obj.collect_on_delivery

    def dehydrate_rider_name_display(self, obj):
        return obj.rider.user.get_full_name() if obj.rider and obj.rider.user else "-"

    def dehydrate_rider_id_display(self, obj):
        return obj.rider.rider_id if obj.rider else "-"

    def dehydrate_vehicle_asset_id_display(self, obj):
        if obj.rider and obj.rider.vehicle_asset:
            return obj.rider.vehicle_asset.asset_id
        return "-"

    def dehydrate_rider_earning(self, obj):
        if hasattr(obj, "rider_earning"):
            return obj.rider_earning.net_earning
        return 0.00


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    """Admin configuration for Order model."""

    resource_classes = [OrderResource]

    actions = [complete_order_for_rider]

    list_display = [
        "order_number",
        "user",
        "rider",
        "get_rider_id",
        "get_rider_earning",
        "mode",
        "is_relay_order",
        "vehicle",
        "get_vehicle_asset_id",
        "status",
        "payment_status",
        "payment_method",
        "total_amount",
        "distance_km",
        "duration_minutes",
        "assigned_at",
        "picked_up_at",
        "arrived_at",
        "completed_at",
        "collect_on_delivery",
        "cod_amount",
        "created_at",
    ]
    list_filter = [
        "status",
        "mode",
        "is_relay_order",
        "payment_method",
        AssignedRiderFilter,
        "rider",
        "created_at",
    ]
    date_hierarchy = "created_at"
    search_fields = [
        "order_number",
        "id",
        "user__business_name",
        "user__phone",
        "rider__user__phone",
        "pickup_address",
    ]
    readonly_fields = ["order_number", "get_rider_earning", "created_at", "updated_at"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Order Information",
            {
                "fields": (
                    "order_number",
                    "user",
                    "mode",
                    "status",
                    "rider",
                    "payment_status",
                )
            },
        ),
        (
            "Pickup Details",
            {
                "fields": (
                    "pickup_address",
                    "sender_name",
                    "sender_phone",
                    "pickup_latitude",
                    "pickup_longitude",
                )
            },
        ),
        ("Delivery Details", {"fields": ("vehicle", "payment_method", "total_amount", "get_rider_earning")}),
        ("Additional Information", {"fields": ("notes", "scheduled_pickup_time")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at", "completed_at", "assigned_at")},
        ),
    )

    inlines = [DeliveryInline, OrderLegInline]

    @admin.display(description="Rider ID")
    def get_rider_id(self, obj):
        return obj.rider.rider_id if obj.rider else "-"

    @admin.display(description="Vehicle ID")
    def get_vehicle_asset_id(self, obj):
        if obj.rider and obj.rider.vehicle_asset:
            return obj.rider.vehicle_asset.asset_id
        return "-"

    @admin.display(description="Rider Earning")
    def get_rider_earning(self, obj):
        if hasattr(obj, "rider_earning"):
            return f"₦{obj.rider_earning.net_earning}"
        return "₦0.00"


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """Admin configuration for Delivery model."""

    list_display = [
        "order",
        "sequence",
        "receiver_name",
        "dropoff_address",
        "status",
        "created_at",
        "cod_amount",
    ]
    list_filter = ["status", "package_type", "created_at"]
    search_fields = [
        "order__order_number",
        "receiver_name",
        "receiver_phone",
        "dropoff_address",
    ]
    readonly_fields = ["created_at", "delivered_at"]
    ordering = ["order", "sequence"]

    fieldsets = (
        ("Order Information", {"fields": ("order", "sequence", "status")}),
        (
            "Pickup Details",
            {
                "fields": (
                    "pickup_address",
                    "pickup_latitude",
                    "pickup_longitude",
                    "sender_name",
                    "sender_phone",
                )
            },
        ),
        (
            "Dropoff Details",
            {
                "fields": (
                    "dropoff_address",
                    "dropoff_latitude",
                    "dropoff_longitude",
                    "receiver_name",
                    "receiver_phone",
                )
            },
        ),
        ("Package Information", {"fields": ("package_type", "notes")}),
        ("Timestamps", {"fields": ("created_at", "delivered_at")}),
    )


@admin.register(OrderLeg)
class OrderLegAdmin(admin.ModelAdmin):
    """Standalone admin view for relay order legs."""

    list_display = [
        "order",
        "leg_number",
        "status",
        "rider",
        "start_relay_node",
        "end_relay_node",
        "distance_km",
        "rider_payout",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["order__order_number", "rider__rider_id", "hub_pin"]
    readonly_fields = ["id", "hub_pin", "created_at"]
    ordering = ["order", "leg_number"]
