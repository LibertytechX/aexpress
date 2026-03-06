from django.contrib import admin
from .models import (
    RideToOwnConfig,
    RideToOwnEnrollment,
    RiderMonthlyTarget,
    RiderStreak,
    Challenge,
    RiderChallengeProgress,
    LeaderboardEntry,
)


@admin.register(RideToOwnConfig)
class RideToOwnConfigAdmin(admin.ModelAdmin):
    list_display = (
        "total_orders_target",
        "program_duration_months",
        "is_active",
        "updated_at",
    )
    list_editable = ("is_active",)


@admin.register(RideToOwnEnrollment)
class RideToOwnEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "rider",
        "vehicle_asset",
        "start_date",
        "end_date",
        "is_active",
        "completed_at",
    )
    list_filter = ("is_active",)
    search_fields = ("rider__rider_id", "rider__user__contact_name")
    raw_id_fields = ("rider", "vehicle_asset")
    readonly_fields = ("created_at", "updated_at")


@admin.register(RiderMonthlyTarget)
class RiderMonthlyTargetAdmin(admin.ModelAdmin):
    list_display = (
        "rider",
        "month",
        "target_earnings",
        "target_orders_per_day",
        "is_auto",
    )
    list_filter = ("month", "is_auto")
    search_fields = ("rider__rider_id", "rider__user__contact_name")
    raw_id_fields = ("rider",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(RiderStreak)
class RiderStreakAdmin(admin.ModelAdmin):
    list_display = (
        "rider",
        "current_streak",
        "longest_streak",
        "last_streak_date",
        "updated_at",
    )
    search_fields = ("rider__rider_id",)
    readonly_fields = ("updated_at",)


class RiderChallengeProgressInline(admin.TabularInline):
    model = RiderChallengeProgress
    extra = 0
    readonly_fields = (
        "rider",
        "current_value",
        "is_completed",
        "completed_at",
        "reward_paid",
        "updated_at",
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "icon_emoji",
        "name",
        "metric",
        "metric_target",
        "reward_type",
        "reward_amount",
        "period",
        "is_active",
        "valid_from",
        "valid_to",
    )
    list_filter = ("is_active", "metric", "period", "reward_type")
    search_fields = ("name",)
    inlines = [RiderChallengeProgressInline]
    fieldsets = (
        ("Basic Info", {"fields": ("name", "description", "icon_emoji", "is_active")}),
        ("Reward", {"fields": ("reward_type", "reward_amount", "reward_perk")}),
        (
            "Metric & Target",
            {"fields": ("metric", "metric_target", "metric_condition")},
        ),
        ("Period", {"fields": ("period", "valid_from", "valid_to")}),
    )


@admin.register(RiderChallengeProgress)
class RiderChallengeProgressAdmin(admin.ModelAdmin):
    list_display = (
        "rider",
        "challenge",
        "current_value",
        "pct_complete",
        "is_completed",
        "reward_paid",
    )
    list_filter = ("is_completed", "reward_paid", "challenge")
    search_fields = ("rider__rider_id",)
    readonly_fields = ("pct_complete", "created_at", "updated_at")
    actions = ["mark_reward_paid"]

    def mark_reward_paid(self, request, queryset):
        queryset.update(reward_paid=True)

    mark_reward_paid.short_description = "Mark selected rewards as paid"


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = (
        "rank",
        "rider",
        "period_type",
        "period_key",
        "trips_count",
        "earnings",
        "rebuilt_at",
    )
    list_filter = ("period_type", "period_key")
    search_fields = ("rider__rider_id",)
    readonly_fields = ("rebuilt_at",)

    def has_add_permission(self, request):
        return False  # Managed by rebuild_leaderboard command only
