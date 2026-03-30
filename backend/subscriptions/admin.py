from django.contrib import admin
from .models import (
    SubscriptionPlan,
    MerchantSubscription,
    SubscriptionUsage,
    SubscriptionOverage,
    SubscriptionInvoice,
    MerchantDedicatedRider,
    PostpaidPlan,
    MerchantPostpaidSubscription,
    PostpaidInvoice,
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "free_orders_limit",
        "overage_fee",
        "order_credits",
        "has_dedicated_rider",
        "created_at",
    )
    search_fields = ("name",)


@admin.register(MerchantSubscription)
class MerchantSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "merchant",
        "plan",
        "start_date",
        "end_date",
        "status",
        "is_paid",
        "plan_credit",
    )
    list_filter = ("status", "is_paid", "plan")
    search_fields = ("merchant__user__business_name", "merchant__merchant_id")


@admin.register(SubscriptionUsage)
class SubscriptionUsageAdmin(admin.ModelAdmin):
    list_display = (
        "subscription",
        "cycle_start_date",
        "cycle_end_date",
        "used_free_orders",
    )
    list_filter = ("cycle_start_date",)


@admin.register(SubscriptionOverage)
class SubscriptionOverageAdmin(admin.ModelAdmin):
    list_display = ("subscription", "order", "amount", "created_at")
    raw_id_fields = ("order",)


@admin.register(SubscriptionInvoice)
class SubscriptionInvoiceAdmin(admin.ModelAdmin):
    list_display = ("subscription", "total_amount", "status", "created_at")
    list_filter = ("status",)


@admin.register(MerchantDedicatedRider)
class MerchantDedicatedRiderAdmin(admin.ModelAdmin):
    list_display = ("merchant", "rider", "created_at")


@admin.register(PostpaidPlan)
class PostpaidPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "plan_type", "is_active", "created_at")
    list_filter = ("plan_type", "is_active")
    search_fields = ("name",)


@admin.register(MerchantPostpaidSubscription)
class MerchantPostpaidSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "merchant",
        "plan",
        "status",
        "accumulated_amount",
        "current_period_end",
    )
    list_filter = ("status", "plan")
    search_fields = ("merchant__user__business_name", "merchant__merchant_id")


@admin.register(PostpaidInvoice)
class PostpaidInvoiceAdmin(admin.ModelAdmin):
    list_display = ("subscription", "amount", "status", "due_date", "created_at")
    list_filter = ("status",)
    search_fields = ("subscription__merchant__user__business_name", "payment_ref")
