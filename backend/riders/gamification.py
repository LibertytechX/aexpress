"""
Gamification service functions for the Axpress rider app.

These are called from the orders signal handler (orders/signals.py)
whenever an Order status transitions to "Done".
"""

from django.utils import timezone
from django.db import transaction


def update_rider_streak(rider):
    """
    Check today's completed order count for the rider.
    If >= 25 orders completed today, increment streak.
    If streak was already recorded today, skip.
    If last streak date was not yesterday, reset first.
    """
    from orders.models import Order
    from .models import RiderStreak

    today = timezone.now().date()

    streak, _ = RiderStreak.objects.get_or_create(rider=rider)

    # Already recorded today — nothing to do
    if streak.last_streak_date == today:
        return

    # Count completed orders today
    todays_count = Order.objects.filter(
        rider=rider,
        status="Done",
        completed_at__date=today,
    ).count()

    if todays_count < 25:
        # Not yet hit the daily target — don't update streak at all yet
        return

    # Hit target today — check if streak continues
    from datetime import timedelta

    yesterday = today - timedelta(days=1)

    if streak.last_streak_date == yesterday:
        # Continuing the streak
        streak.current_streak += 1
    else:
        # Gap — reset
        streak.current_streak = 1

    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak

    streak.last_streak_date = today
    streak.save()


def update_challenge_progress(rider, order):
    """
    Update all active challenge progress records for this rider
    based on the completed order.
    """
    from .models import RiderChallengeProgress

    today = timezone.now().date()
    active_challenges = _get_active_challenges(today)

    for challenge in active_challenges:
        progress, _ = RiderChallengeProgress.objects.get_or_create(
            rider=rider,
            challenge=challenge,
        )

        if progress.is_completed:
            continue

        new_value = _compute_challenge_value(rider, challenge, order)
        if new_value > progress.current_value:
            progress.current_value = new_value
            if new_value >= challenge.metric_target:
                progress.is_completed = True
                progress.completed_at = timezone.now()
            progress.save()


def _get_active_challenges(today):
    from .models import Challenge
    from django.db.models import Q

    return Challenge.objects.filter(
        is_active=True,
    ).filter(
        Q(valid_from__isnull=True) | Q(valid_from__lte=today),
        Q(valid_to__isnull=True) | Q(valid_to__gte=today),
    )


def _compute_challenge_value(rider, challenge, order):
    """
    Compute the current progress value for a rider on a challenge,
    based on the challenge metric type.
    """
    from orders.models import Order
    from .models import Challenge, RiderStreak
    from datetime import timedelta

    today = timezone.now().date()
    metric = challenge.metric
    condition = challenge.metric_condition or {}

    if metric == Challenge.Metric.ORDERS_COUNT_DAY:
        # E.g. Early Bird: 5 orders before 9 AM
        before_hour = condition.get("before_hour", None)
        if before_hour:
            count = Order.objects.filter(
                rider=rider,
                status="Done",
                completed_at__date=today,
                completed_at__hour__lt=before_hour,
            ).count()
        else:
            count = Order.objects.filter(
                rider=rider,
                status="Done",
                completed_at__date=today,
            ).count()
        return count

    elif metric == Challenge.Metric.ORDERS_COUNT_WEEK:
        # E.g. Century Club: 100 orders this week
        week_start = today - timedelta(days=today.weekday())
        count = Order.objects.filter(
            rider=rider,
            status="Done",
            completed_at__date__gte=week_start,
            completed_at__date__lte=today,
        ).count()
        return count

    elif metric == Challenge.Metric.STREAK_DAYS:
        # E.g. 7-Day Streak
        try:
            streak = RiderStreak.objects.get(rider=rider)
            return streak.current_streak
        except RiderStreak.DoesNotExist:
            return 0

    elif metric == Challenge.Metric.NO_CANCELLATIONS:
        # Count consecutive days without a rider cancellation
        # Use completed_at date of enrollment minus any RiderCanceled orders
        period_days = challenge.metric_target  # e.g. 30
        period_start = today - timedelta(days=period_days)
        cancellations = Order.objects.filter(
            rider=rider,
            status="RiderCanceled",
            canceled_at__date__gte=period_start,
        ).count()
        if cancellations == 0:
            # Track days since last cancellation
            last_cancel = (
                Order.objects.filter(
                    rider=rider,
                    status="RiderCanceled",
                )
                .order_by("-canceled_at")
                .first()
            )
            if last_cancel is None:
                # No cancellations ever — use days since first order
                first_order = (
                    Order.objects.filter(rider=rider, status="Done")
                    .order_by("completed_at")
                    .first()
                )
                if first_order:
                    return (today - first_order.completed_at.date()).days
                return 0
            else:
                return (today - last_cancel.canceled_at.date()).days
        return 0

    elif metric == Challenge.Metric.REFERRALS_COUNT:
        # Count active referrals this period
        try:
            from referrals.models import RiderReferral

            period = challenge.period
            if period == Challenge.Period.MONTHLY:
                import calendar

                month_start = today.replace(day=1)
                count = RiderReferral.objects.filter(
                    referring_rider=rider,
                    created_at__date__gte=month_start,
                ).count()
            else:
                count = RiderReferral.objects.filter(referring_rider=rider).count()
            return count
        except Exception:
            return 0

    return 0
