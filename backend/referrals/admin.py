from django.contrib import admin
from .models import RiderReferral, ReferralEarning


class ReferralEarningInline(admin.TabularInline):
    model = ReferralEarning
    extra = 0
    readonly_fields = ("order", "commission_amount", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(RiderReferral)
class RiderReferralAdmin(admin.ModelAdmin):
    list_display = (
        "referring_rider",
        "merchant",
        "status",
        "created_at",
        "activated_at",
    )
    list_filter = ("status",)
    search_fields = (
        "referring_rider__rider_id",
        "merchant__business_name",
        "merchant__phone",
    )
    raw_id_fields = ("referring_rider", "merchant")
    readonly_fields = ("created_at", "activated_at")
    inlines = [ReferralEarningInline]


@admin.register(ReferralEarning)
class ReferralEarningAdmin(admin.ModelAdmin):
    list_display = ("referral", "order", "commission_amount", "created_at")
    search_fields = ("referral__referring_rider__rider_id", "order__order_number")
    readonly_fields = ("created_at",)

    def has_add_permission(self, request):
        return False  # Created only via the commission service
