"""
Gamification API views for the riders app.
All views require rider authentication (RiderIsAuthenticated permission).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone

from orders.permissions import IsRider
from .models import (
    RideToOwnEnrollment,
    RiderMonthlyTarget,
    RiderChallengeProgress,
    LeaderboardEntry,
    RiderStreak,
    Challenge,
)


def get_rider(user):
    """Helper to get rider profile from user."""
    return getattr(user, "rider_profile", None)


# ---------------------------------------------------------------------------
# Ride to Own
# ---------------------------------------------------------------------------


class RideToOwnView(APIView):
    """
    GET /api/riders/ride-to-own/
    Returns the rider's Ride to Own progress.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        rider = get_rider(request.user)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            enrollment = RideToOwnEnrollment.objects.get(rider=rider, is_active=True)
        except RideToOwnEnrollment.DoesNotExist:
            return Response(
                {"enrolled": False, "message": "You are not enrolled in Ride to Own."},
                status=status.HTTP_200_OK,
            )

        progress = enrollment.get_progress()
        vehicle = enrollment.vehicle_asset
        return Response(
            {
                "enrolled": True,
                "vehicle": {
                    "asset_id": vehicle.asset_id if vehicle else None,
                    "make": vehicle.make if vehicle else None,
                    "model": vehicle.model if vehicle else None,
                    "plate_number": vehicle.plate_number if vehicle else None,
                    "photo": vehicle.photo if vehicle else None,
                },
                **progress,
            }
        )


# ---------------------------------------------------------------------------
# Monthly Target
# ---------------------------------------------------------------------------


class MonthlyTargetView(APIView):
    """
    GET /api/riders/monthly-target/
    Returns the rider's current month target, progress, daily chart, milestones.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        rider = get_rider(request.user)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        today = timezone.now().date()
        current_month = today.replace(day=1)

        try:
            target = RiderMonthlyTarget.objects.get(rider=rider, month=current_month)
        except RiderMonthlyTarget.DoesNotExist:
            return Response(
                {
                    "has_target": False,
                    "message": "No monthly target set for this month.",
                },
                status=status.HTTP_200_OK,
            )

        progress = target.get_progress()

        # Today's mission: orders needed today to stay on pace
        from orders.models import Order

        todays_done = Order.objects.filter(
            rider=rider, status="Done", completed_at__date=today
        ).count()
        orders_needed_today = max(target.target_orders_per_day - todays_done, 0)
        avg_earning_per_order = float(progress["earned"]) / max(
            Order.objects.filter(
                rider=rider, status="Done", completed_at__date__gte=current_month
            ).count(),
            1,
        )
        today_mission = {
            "done_today": todays_done,
            "target_today": target.target_orders_per_day,
            "orders_needed": orders_needed_today,
            "estimated_earnings_needed": round(
                orders_needed_today * avg_earning_per_order, 2
            ),
            "avg_earning_per_order": round(avg_earning_per_order, 2),
        }

        return Response(
            {
                "has_target": True,
                "today_mission": today_mission,
                **progress,
            }
        )


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------


class ChallengeListView(APIView):
    """
    GET /api/riders/challenges/
    Returns active and completed challenges for the rider.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        rider = get_rider(request.user)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        today = timezone.now().date()

        from .gamification import _get_active_challenges

        active_challenges = _get_active_challenges(today)

        # Ensure progress records exist for all active challenges
        for challenge in active_challenges:
            RiderChallengeProgress.objects.get_or_create(
                rider=rider, challenge=challenge
            )

        progress_qs = (
            RiderChallengeProgress.objects.filter(rider=rider)
            .select_related("challenge")
            .order_by("is_completed", "-updated_at")
        )

        active = []
        completed = []

        for p in progress_qs:
            ch = p.challenge
            entry = {
                "id": str(ch.id),
                "name": ch.name,
                "description": ch.description,
                "icon_emoji": ch.icon_emoji,
                "reward_type": ch.reward_type,
                "reward_amount": ch.reward_amount,
                "reward_perk": ch.reward_perk,
                "metric": ch.metric,
                "metric_target": ch.metric_target,
                "current_value": p.current_value,
                "pct_complete": p.pct_complete,
                "is_completed": p.is_completed,
                "completed_at": p.completed_at,
                "reward_paid": p.reward_paid,
            }
            if p.is_completed:
                completed.append(entry)
            else:
                active.append(entry)

        return Response(
            {
                "active": active,
                "completed": completed,
            }
        )


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------


class LeaderboardView(APIView):
    """
    GET /api/riders/leaderboard/?period=this_week|this_month|all_time
    Returns a ranked list of riders for the given period.
    The current rider's entry is highlighted.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        rider = get_rider(request.user)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        period = request.query_params.get("period", "this_month")

        valid_periods = {
            LeaderboardEntry.PeriodType.THIS_WEEK,
            LeaderboardEntry.PeriodType.THIS_MONTH,
            LeaderboardEntry.PeriodType.ALL_TIME,
        }
        if period not in valid_periods:
            period = LeaderboardEntry.PeriodType.THIS_MONTH

        today = timezone.now().date()
        if period == LeaderboardEntry.PeriodType.THIS_WEEK:
            period_key = today.strftime("%Y-W%W")
        elif period == LeaderboardEntry.PeriodType.THIS_MONTH:
            period_key = today.strftime("%Y-%m")
        else:
            period_key = "all_time"

        entries = (
            LeaderboardEntry.objects.filter(
                period_type=period,
                period_key=period_key,
            )
            .select_related("rider__user")
            .order_by("rank")[:50]
        )

        result = []
        my_entry = None
        for entry in entries:
            r = entry.rider
            item = {
                "rank": entry.rank,
                "rider_id": r.rider_id,
                "name": r.user.contact_name or r.user.phone,
                "zone": entry.zone_name,
                "trips_count": entry.trips_count,
                "earnings": entry.earnings,
                "is_me": r.id == rider.id,
            }
            result.append(item)
            if r.id == rider.id:
                my_entry = item

        return Response(
            {
                "period": period,
                "period_key": period_key,
                "my_rank": my_entry["rank"] if my_entry else None,
                "entries": result,
            }
        )


# ---------------------------------------------------------------------------
# Dashboard Summary Card
# ---------------------------------------------------------------------------


class DashboardSummaryView(APIView):
    """
    GET /api/riders/dashboard-summary/
    Returns a compact summary for the home screen widget:
    - Monthly target progress
    - Day streak + milestone hint
    - Leaderboard rank
    - Referral count + earnings
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        rider = get_rider(request.user)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        today = timezone.now().date()
        current_month = today.replace(day=1)

        # Monthly target
        monthly_pct = None
        monthly_earned = None
        monthly_target = None
        is_behind = None
        try:
            mt = RiderMonthlyTarget.objects.get(rider=rider, month=current_month)
            p = mt.get_progress()
            monthly_pct = p["pct_complete"]
            monthly_earned = float(p["earned"])
            monthly_target = float(p["target_earnings"])
            is_behind = p["is_behind"]
        except RiderMonthlyTarget.DoesNotExist:
            pass

        # Streak
        current_streak = 0
        streak_next_milestone = None
        streak_next_reward = None
        try:
            s = rider.streak
            current_streak = s.current_streak
            # Find next challenge milestone for streak
            streak_challenge = (
                Challenge.objects.filter(
                    is_active=True,
                    metric=Challenge.Metric.STREAK_DAYS,
                )
                .order_by("metric_target")
                .first()
            )
            if streak_challenge:
                streak_next_milestone = streak_challenge.metric_target
                streak_next_reward = streak_challenge.reward_amount
        except Exception:
            pass

        # Leaderboard rank this month
        period_key = today.strftime("%Y-%m")
        leaderboard_rank = None
        try:
            entry = LeaderboardEntry.objects.get(
                rider=rider,
                period_type=LeaderboardEntry.PeriodType.THIS_MONTH,
                period_key=period_key,
            )
            leaderboard_rank = entry.rank
        except LeaderboardEntry.DoesNotExist:
            pass

        # Referrals
        referral_count = 0
        referral_earnings = 0
        try:
            from referrals.models import RiderReferral, ReferralEarning
            from django.db.models import Sum

            referral_count = RiderReferral.objects.filter(referring_rider=rider).count()
            referral_earnings = float(
                ReferralEarning.objects.filter(
                    referral__referring_rider=rider
                ).aggregate(total=Sum("commission_amount"))["total"]
                or 0
            )
        except Exception:
            pass

        return Response(
            {
                "monthly_target": {
                    "pct_complete": monthly_pct,
                    "earned": monthly_earned,
                    "target": monthly_target,
                    "is_behind": is_behind,
                },
                "streak": {
                    "current": current_streak,
                    "next_milestone": streak_next_milestone,
                    "next_milestone_reward": streak_next_reward,
                },
                "leaderboard": {
                    "rank": leaderboard_rank,
                    "is_top_3": leaderboard_rank is not None and leaderboard_rank <= 3,
                },
                "referrals": {
                    "count": referral_count,
                    "total_earnings": referral_earnings,
                },
            }
        )
