import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from sparky_utils.exceptions import ServiceException

from dispatcher.models import (
    DispatcherProfile,
    DispatcherCommission,
    DispatcherMonthlyEarning,
    Rider,
    SystemSettings,
)

logger = logging.getLogger(__name__)

DEFAULT_COMMISSION_PER_ORDER = Decimal("3000.00")


def get_current_month_str(dt: Optional[datetime] = None) -> str:
    """Return string representation of month in YYYY-MM format."""
    target_dt = dt or timezone.now()
    return target_dt.strftime("%Y-%m")


def get_previous_month_str(dt: Optional[datetime] = None) -> str:
    """Return string representation of previous month in YYYY-MM format."""
    target_dt = dt or timezone.now()
    first_of_month = target_dt.replace(day=1)
    prev_month_end = first_of_month - timezone.timedelta(days=1)
    return prev_month_end.strftime("%Y-%m")


def affiliate_rider_to_dispatcher(rider: Rider, affiliation_code: str) -> DispatcherProfile:
    """
    Affiliates a rider with a dispatcher using the dispatcher's unique affiliation code.
    Raises ServiceException if code is invalid or rider is already affiliated.
    """
    if not affiliation_code or not affiliation_code.strip():
        raise ServiceException(
            status_code=400,
            message="Affiliation code is required."
        )

    code_clean = affiliation_code.strip().upper()
    try:
        dispatcher = DispatcherProfile.objects.select_related("user").get(
            affiliation_code__iexact=code_clean
        )
    except DispatcherProfile.DoesNotExist:
        raise ServiceException(
            status_code=400,
            message="Invalid affiliation code. No dispatcher found with this code."
        )

    if rider.is_affiliated and rider.affiliated_to_id:
        if rider.affiliated_to_id == dispatcher.id:
            raise ServiceException(
                status_code=400,
                message="You are already affiliated with this dispatcher."
            )
        else:
            current_dispatcher_name = (
                rider.affiliated_to.user.contact_name
                or rider.affiliated_to.user.phone
                if rider.affiliated_to.user
                else "another dispatcher"
            )
            raise ServiceException(
                status_code=400,
                message=f"You are already affiliated with {current_dispatcher_name}."
            )

    rider.affiliated_to = dispatcher
    rider.is_affiliated = True
    rider.affiliated_at = timezone.now()
    rider.save(update_fields=["affiliated_to", "is_affiliated", "affiliated_at"])

    logger.info(
        f"Rider {rider.rider_id} successfully affiliated to dispatcher {dispatcher.id} (code: {code_clean})"
    )
    return dispatcher


def record_dispatcher_affiliation_commission(order) -> Optional[DispatcherCommission]:
    """
    Records an immutable commission entry for the dispatcher affiliated with the order's rider
    upon successful order completion ('Done').
    
    Guarantees:
    - Atomicity & Concurrency: uses database row-level locking (select_for_update).
    - Idempotency: checks unique constraint on (dispatcher, order).
    - Automatic monthly rollover: handles transitions across calendar months.
    """
    if not order or not getattr(order, "rider", None):
        return None

    rider = order.rider
    if not rider.is_affiliated or not rider.affiliated_to:
        return None

    dispatcher = rider.affiliated_to

    # Check if commission was already generated for this order
    existing = DispatcherCommission.objects.filter(
        dispatcher=dispatcher,
        order=order,
    ).first()
    if existing:
        logger.info(
            f"Dispatcher commission already recorded for order {order.order_number} and dispatcher {dispatcher.id}"
        )
        return existing

    # Determine commission amount from SystemSettings or fallback default (3000)
    settings = SystemSettings.objects.first()
    commission_amount = (
        getattr(settings, "affiliation_commission_per_order", None)
        or DEFAULT_COMMISSION_PER_ORDER
    )

    completion_dt = order.completed_at or timezone.now()
    order_month_str = get_current_month_str(completion_dt)
    current_calendar_month = get_current_month_str()

    with transaction.atomic():
        # Concurrency safety: lock DispatcherProfile
        profile = (
            DispatcherProfile.objects.select_for_update()
            .select_related("user")
            .get(id=dispatcher.id)
        )

        # Check for month rollover
        if profile.last_commission_month and profile.last_commission_month != current_calendar_month:
            profile.previous_month_commission = profile.monthly_commission
            profile.monthly_commission = Decimal("0.00")
            profile.last_commission_month = current_calendar_month
        elif not profile.last_commission_month:
            profile.last_commission_month = current_calendar_month

        commission, created = DispatcherCommission.objects.get_or_create(
            dispatcher=profile,
            order=order,
            defaults={
                "rider": rider,
                "order_number": getattr(order, "order_number", "") or str(order.id),
                "amount": commission_amount,
                "month_year": order_month_str,
                "description": f"Affiliation commission for completed order #{order.order_number} by rider {rider.rider_id}",
            },
        )

        if not created:
            return commission

        # Accumulate to active monthly commission if belonging to current active month
        if order_month_str == profile.last_commission_month:
            profile.monthly_commission = (
                profile.monthly_commission + commission_amount
            )
        profile.total_commission_earned = (
            profile.total_commission_earned + commission_amount
        )
        profile.save(
            update_fields=[
                "monthly_commission",
                "previous_month_commission",
                "total_commission_earned",
                "last_commission_month",
                "updated_at",
            ]
        )

        # Update or create monthly earnings ledger summary
        monthly_earning, _ = DispatcherMonthlyEarning.objects.select_for_update().get_or_create(
            dispatcher=profile,
            month_year=order_month_str,
            defaults={
                "total_orders": 0,
                "total_commission": Decimal("0.00"),
                "status": DispatcherMonthlyEarning.SettlementStatus.ACCUMULATING,
            },
        )
        monthly_earning.total_orders += 1
        monthly_earning.total_commission += commission_amount
        monthly_earning.save(update_fields=["total_orders", "total_commission", "updated_at"])

    logger.info(
        f"Recorded ₦{commission_amount} commission for dispatcher {profile.id} from order {order.order_number} (rider {rider.rider_id})"
    )
    return commission


def reconcile_dispatcher_monthly_commission(
    dispatcher: DispatcherProfile,
    month_year: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reconciles all commission entries for a dispatcher in a given month.
    Ensures mathematical consistency between individual DispatcherCommission rows,
    the DispatcherMonthlyEarning summary, and DispatcherProfile commission caches.
    """
    target_month = month_year or get_current_month_str()
    current_calendar_month = get_current_month_str()
    prev_calendar_month = get_previous_month_str()

    with transaction.atomic():
        profile = (
            DispatcherProfile.objects.select_for_update()
            .get(id=dispatcher.id)
        )

        entries = DispatcherCommission.objects.filter(
            dispatcher=profile,
            month_year=target_month,
        )
        actual_total = (
            entries.aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")
        )
        actual_orders = entries.count()

        monthly_earning, _ = DispatcherMonthlyEarning.objects.select_for_update().get_or_create(
            dispatcher=profile,
            month_year=target_month,
            defaults={
                "total_orders": actual_orders,
                "total_commission": actual_total,
                "status": DispatcherMonthlyEarning.SettlementStatus.ACCUMULATING,
            },
        )
        monthly_earning.total_orders = actual_orders
        monthly_earning.total_commission = actual_total
        monthly_earning.save(update_fields=["total_orders", "total_commission", "updated_at"])

        # Sync profile caches
        update_fields = ["total_commission_earned", "updated_at"]
        all_time_total = (
            DispatcherCommission.objects.filter(dispatcher=profile).aggregate(
                Sum("amount")
            )["amount__sum"]
            or Decimal("0.00")
        )
        profile.total_commission_earned = all_time_total

        if target_month == current_calendar_month:
            profile.monthly_commission = actual_total
            profile.last_commission_month = current_calendar_month
            update_fields.extend(["monthly_commission", "last_commission_month"])
        elif target_month == prev_calendar_month:
            profile.previous_month_commission = actual_total
            update_fields.append("previous_month_commission")

        profile.save(update_fields=update_fields)

    return {
        "dispatcher_id": str(profile.id),
        "month_year": target_month,
        "total_orders": actual_orders,
        "total_commission": str(actual_total),
        "all_time_total": str(all_time_total),
        "reconciled": True,
    }


def reset_monthly_commissions_service() -> int:
    """
    Rolls over monthly commissions for all dispatchers on month boundaries.
    Moves monthly_commission into previous_month_commission and resets monthly_commission to 0.00.
    Returns the count of dispatchers updated.
    """
    current_calendar_month = get_current_month_str()
    dispatchers_to_reset = DispatcherProfile.objects.exclude(
        last_commission_month=current_calendar_month
    )

    count = 0
    with transaction.atomic():
        for profile in dispatchers_to_reset.select_for_update():
            profile.previous_month_commission = profile.monthly_commission
            profile.monthly_commission = Decimal("0.00")
            profile.last_commission_month = current_calendar_month
            profile.save(
                update_fields=[
                    "previous_month_commission",
                    "monthly_commission",
                    "last_commission_month",
                    "updated_at",
                ]
            )
            count += 1

    logger.info(
        f"reset_monthly_commissions_service: Rolled over {count} dispatchers to month {current_calendar_month}"
    )
    return count
