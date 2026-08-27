"""
OrderMetrics — status normalization + counts.

The single place the real `orders.Order` status enum is mapped to logical
buckets, so every dashboard agrees on what "delivered" / "cancelled" / etc. mean.

Real status enum (orders.Order.STATUS_CHOICES):
    Pending, Assigned, AssignmentAccepted, AssignmentRejected, Started,
    Pickup, Fulfilling, Arrived, Done, CustomerCanceled, RiderCanceled, Failed
"""

from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce

ZERO = Decimal("0")

# ── Canonical status groups ─────────────────────────────────────────
DELIVERED_STATUSES = ["Done"]
CANCELLED_STATUSES = ["CustomerCanceled", "RiderCanceled"]
FAILED_STATUSES = ["Failed"]
REJECTED_STATUSES = ["AssignmentRejected"]
PENDING_STATUSES = ["Pending"]
IN_PROGRESS_STATUSES = [
    "Assigned",
    "AssignmentAccepted",
    "Started",
    "Pickup",
    "Fulfilling",
    "Arrived",
]

# Terminal = no longer in flight.
TERMINAL_STATUSES = DELIVERED_STATUSES + CANCELLED_STATUSES + FAILED_STATUSES


def order_status_counts(qs):
    """Return all logical status-bucket counts in a single aggregate."""
    return qs.aggregate(
        total=Count("id"),
        delivered=Count("id", filter=Q(status__in=DELIVERED_STATUSES)),
        cancelled=Count("id", filter=Q(status__in=CANCELLED_STATUSES)),
        failed=Count("id", filter=Q(status__in=FAILED_STATUSES)),
        rejected=Count("id", filter=Q(status__in=REJECTED_STATUSES)),
        pending=Count("id", filter=Q(status__in=PENDING_STATUSES)),
        in_progress=Count("id", filter=Q(status__in=IN_PROGRESS_STATUSES)),
    )


def _commission_pct():
    """Platform/rider commission rate (%) from SystemSettings (default 20)."""
    from dispatcher.models import SystemSettings

    s = SystemSettings.objects.first()
    if s and s.commission_pct is not None:
        return Decimal(s.commission_pct)
    return Decimal("20")


def _pct(part, whole):
    return round(part / whole * 100, 1) if whole else 0.0


def order_dashboard(qs, top=10):
    """
    Consolidated order metrics at three levels (single aggregate per section):
      - management : status funnel + rates + revenue/AOV + rider commission
      - by_rider   : per-rider orders / delivered / completion / revenue / commission
      - by_merchant: per-merchant orders / delivered / completion / GMV / AOV
    `qs` is an already period-scoped Order queryset.
    """
    pct_rate = _commission_pct()
    counts = order_status_counts(qs)
    total, delivered = counts["total"], counts["delivered"]
    revenue = qs.aggregate(
        r=Coalesce(Sum("total_amount", filter=Q(status__in=DELIVERED_STATUSES)), ZERO)
    )["r"]
    aov = (revenue / delivered) if delivered else ZERO
    commission_total = revenue * pct_rate / Decimal("100")

    management = {
        "total_orders": total,
        "delivered": delivered,
        "in_progress": counts["in_progress"],
        "pending": counts["pending"],
        "cancelled": counts["cancelled"],
        "failed": counts["failed"],
        "rejected": counts["rejected"],
        "completion_rate": _pct(delivered, total),
        "cancellation_rate": _pct(counts["cancelled"], total),
        "gross_revenue": str(revenue),
        "avg_order_value": str(aov.quantize(Decimal("0.01"))),
        "rider_commission_total": str(commission_total.quantize(Decimal("0.01"))),
        "commission_pct": str(pct_rate),
    }

    by_rider = []
    for r in (
        qs.filter(rider__isnull=False)
        .values("rider__rider_id", "rider__user__contact_name")
        .annotate(
            orders=Count("id"),
            delivered=Count("id", filter=Q(status__in=DELIVERED_STATUSES)),
            cancelled=Count("id", filter=Q(status__in=CANCELLED_STATUSES)),
            revenue=Coalesce(
                Sum("total_amount", filter=Q(status__in=DELIVERED_STATUSES)), ZERO
            ),
        )
        .order_by("-revenue")[:top]
    ):
        rev = r["revenue"]
        by_rider.append({
            "rider_id": r["rider__rider_id"],
            "name": r["rider__user__contact_name"],
            "orders": r["orders"],
            "delivered": r["delivered"],
            "cancelled": r["cancelled"],
            "completion_rate": _pct(r["delivered"], r["orders"]),
            "revenue": str(rev),
            "commission": str(
                (rev * pct_rate / Decimal("100")).quantize(Decimal("0.01"))
            ),
        })

    by_merchant = []
    for m in (
        qs.values("user__business_name")
        .annotate(
            orders=Count("id"),
            delivered=Count("id", filter=Q(status__in=DELIVERED_STATUSES)),
            cancelled=Count("id", filter=Q(status__in=CANCELLED_STATUSES)),
            revenue=Coalesce(
                Sum("total_amount", filter=Q(status__in=DELIVERED_STATUSES)), ZERO
            ),
        )
        .order_by("-revenue")[:top]
    ):
        rev, dl = m["revenue"], m["delivered"]
        by_merchant.append({
            "merchant": m["user__business_name"],
            "orders": m["orders"],
            "delivered": dl,
            "cancelled": m["cancelled"],
            "completion_rate": _pct(dl, m["orders"]),
            "gmv": str(rev),
            "avg_order_value": str(
                (rev / dl).quantize(Decimal("0.01")) if dl else ZERO
            ),
        })

    return {
        "management": management,
        "by_rider": by_rider,
        "by_merchant": by_merchant,
    }
