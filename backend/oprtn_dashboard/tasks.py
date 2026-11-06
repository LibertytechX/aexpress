"""
Celery tasks for the Operations Dashboard app.

  - generate_alerts: run the alert engine. Wired onto CELERY_BEAT_SCHEDULE
    to run every 30 minutes (an optional ~2 min fast lane for
    BIKE_AFTER_HOURS / SPEED_VIOLATION / GHOST_RIDE is available). See guide §14.8.
"""

from celery import shared_task


@shared_task
def generate_alerts(only_types=None):
    """Evaluate enabled alert rules and reconcile alerts. Returns a summary."""
    from .alerts.engine import run_all_rules

    return run_all_rules(only_types=only_types)


# Filters to pre-warm. Keys match what filters.parse_filter produces so the
# endpoints' read-through cache actually hits these snapshots.
_WARM_FILTERS = [
    ("today", "today"),
    ("this_week", "this_week"),
    ("this_month", "this_month"),
    ("this_year", "annually"),
]


@shared_task
def refresh_dashboard_cache():
    """
    Pre-compute payments / COD / fuel dashboard payloads for the common filters
    and store them in the cache. Runs every 30 min so dashboard reads are fast.
    """
    from dispatcher.periods import _parse_period
    from orders.models import Order

    from .caching import set_cached
    from .metrics import (
        cod_metrics,
        fuel_metrics,
        order_metrics,
        payment_metrics,
    )
    from .models import FuelBill

    warmed = {}
    for period, label in _WARM_FILTERS:
        start, end, _ = _parse_period(period)
        desc = {
            "filter": label,
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        order_qs = Order.objects.filter(
            created_at__gte=start, created_at__lte=end
        )
        fuel_qs = FuelBill.objects.filter(
            bill_date__gte=start.date(), bill_date__lte=end.date()
        )
        set_cached("payments", desc, payment_metrics.payment_breakdown(order_qs))
        set_cached("cod-dashboard", desc, cod_metrics.cod_dashboard(order_qs))
        set_cached("order-dashboard", desc, order_metrics.order_dashboard(order_qs))
        set_cached("fuel-dashboard", desc, fuel_metrics.fuel_dashboard(fuel_qs))
        warmed[label] = "ok"
    return {"warmed": warmed}
