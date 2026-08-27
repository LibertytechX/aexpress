"""
PaymentMetrics — order amount across **all** payment types.

Source of truth: `orders.Order.total_amount` (the delivery charge = revenue),
grouped by `payment_method` and `payment_status`, plus a cash-flow-timing split
so the dashboard is honest about *when* money is actually in hand.

Payment methods (orders.Order.PAYMENT_METHOD_CHOICES):
    wallet, cash, cash_on_pickup, receiver_pays, postpaid, subscription
"""

from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce

from .order_metrics import DELIVERED_STATUSES

ZERO = Decimal("0")

# Cash-flow semantics: when is the money actually collected?
COLLECTION_TIMING = {
    "wallet": "prepaid",  # escrow-funded up front
    "cash": "rider_collected",
    "cash_on_pickup": "rider_collected",
    "receiver_pays": "rider_collected",
    "postpaid": "deferred",  # billed later
    "subscription": "deferred",
}


def _pct(part, whole):
    return round(float(part) / float(whole) * 100, 1) if whole else 0.0


def payment_breakdown(qs):
    """
    Return order-amount totals across every payment method/status plus a
    collection-timing split. `qs` is an already period-scoped Order queryset.
    """
    summary = qs.aggregate(
        total_orders=Count("id"),
        amount_sum=Coalesce(Sum("total_amount"), ZERO),
        recognized_revenue=Coalesce(
            Sum("total_amount", filter=Q(status__in=DELIVERED_STATUSES)),
            ZERO,
        ),
    )
    total_amount = summary["amount_sum"]

    by_method = []
    timing_totals = {"prepaid": ZERO, "rider_collected": ZERO, "deferred": ZERO,
                     "other": ZERO}
    method_rows = (
        qs.values("payment_method")
        .annotate(count=Count("id"), amount=Coalesce(Sum("total_amount"), ZERO))
        .order_by("-amount")
    )
    for row in method_rows:
        method = row["payment_method"]
        amount = row["amount"]
        timing = COLLECTION_TIMING.get(method, "other")
        timing_totals[timing] += amount
        by_method.append(
            {
                "payment_method": method,
                "count": row["count"],
                "amount": str(amount),
                "pct": _pct(amount, total_amount),
                "collection_timing": timing,
            }
        )

    by_status = [
        {
            "payment_status": row["payment_status"],
            "count": row["count"],
            "amount": str(row["amount"]),
            "pct": _pct(row["amount"], total_amount),
        }
        for row in (
            qs.values("payment_status")
            .annotate(
                count=Count("id"), amount=Coalesce(Sum("total_amount"), ZERO)
            )
            .order_by("-amount")
        )
    ]

    by_timing = {
        timing: {"amount": str(amt), "pct": _pct(amt, total_amount)}
        for timing, amt in timing_totals.items()
    }

    return {
        "total_orders": summary["total_orders"],
        "total_amount": str(total_amount),
        "recognized_revenue": str(summary["recognized_revenue"]),
        "by_method": by_method,
        "by_status": by_status,
        "by_collection_timing": by_timing,
    }
