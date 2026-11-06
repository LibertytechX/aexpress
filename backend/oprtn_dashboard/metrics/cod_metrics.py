"""
CodMetrics — COD goods value, COD **fee**, and collection reconciliation.

Three distinct money buckets, never conflated:
  - delivery charge  = Order.total_amount        (revenue — NOT here)
  - COD goods value  = Order.cod_amount          (pass-through liability)
  - COD fee          = SystemSettings.cod_flat_fee + cod_pct_fee% × cod_amount
                       (AXpress surcharge = additive revenue, derived)

Collected actuals come from `riders.RiderCodRecord`
(status pending/remitted/verified). Outstanding + ageing are reconciled against
those records. The COD fee is "estimated" (derived from config) until a
`cod_fee` column is persisted on the order.
"""

from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from .order_metrics import (
    CANCELLED_STATUSES,
    DELIVERED_STATUSES,
    FAILED_STATUSES,
    IN_PROGRESS_STATUSES,
    PENDING_STATUSES,
)

ZERO = Decimal("0")
HUNDRED = Decimal("100")


def get_cod_fee_config():
    """Return (cod_flat_fee, cod_pct_fee) from SystemSettings, with defaults."""
    from dispatcher.models import SystemSettings

    s = SystemSettings.objects.first()
    if s:
        return Decimal(s.cod_flat_fee), Decimal(s.cod_pct_fee)
    return Decimal("500"), Decimal("1.5")


def cod_fee_for(cod_amount, flat, pct):
    """COD fee for a single order's cod_amount."""
    return flat + (pct / HUNDRED) * (cod_amount or ZERO)


def _pct(part, whole):
    return round(float(part) / float(whole) * 100, 1) if whole else 0.0


def _ageing(cod_qs):
    """Bucket uncollected (pending) COD by age since delivery."""
    from riders.models import RiderCodRecord

    now = timezone.now()
    buckets = {
        "0_24h": {"count": 0, "amount": ZERO},
        "24_48h": {"count": 0, "amount": ZERO},
        "48h_plus": {"count": 0, "amount": ZERO},
    }
    rows = RiderCodRecord.objects.filter(
        order__in=cod_qs, status="pending"
    ).values("amount", "created_at", "order__completed_at")

    for r in rows:
        ref = r["order__completed_at"] or r["created_at"]
        hours = (now - ref).total_seconds() / 3600
        if hours < 24:
            key = "0_24h"
        elif hours < 48:
            key = "24_48h"
        else:
            key = "48h_plus"
        buckets[key]["count"] += 1
        buckets[key]["amount"] += r["amount"] or ZERO

    return {k: {"count": v["count"], "amount": str(v["amount"])}
            for k, v in buckets.items()}


def cod_dashboard(qs):
    """Full COD dashboard payload for a period-scoped Order queryset."""
    from riders.models import RiderCodRecord

    cod_qs = qs.filter(collect_on_delivery=True)
    flat, pct = get_cod_fee_config()

    agg = cod_qs.aggregate(
        total_orders=Count("id"),
        delivered=Count("id", filter=Q(status__in=DELIVERED_STATUSES)),
        in_progress=Count(
            "id", filter=Q(status__in=IN_PROGRESS_STATUSES + PENDING_STATUSES)
        ),
        cancelled=Count(
            "id", filter=Q(status__in=CANCELLED_STATUSES + FAILED_STATUSES)
        ),
        cod_value_total=Coalesce(Sum("cod_amount"), ZERO),
        cod_expected=Coalesce(
            Sum("cod_amount", filter=Q(status__in=DELIVERED_STATUSES)), ZERO
        ),
    )

    delivered = agg["delivered"]
    cod_expected = agg["cod_expected"]
    cod_fees_earned = flat * delivered + (pct / HUNDRED) * cod_expected

    rec_agg = RiderCodRecord.objects.filter(order__in=cod_qs).aggregate(
        collected=Coalesce(
            Sum("amount", filter=Q(status__in=["remitted", "verified"])), ZERO
        ),
        pending=Coalesce(Sum("amount", filter=Q(status="pending")), ZERO),
    )
    cod_collected = rec_agg["collected"]
    cod_outstanding = cod_expected - cod_collected

    cards = {
        "total_orders": agg["total_orders"],
        "delivered": delivered,
        "in_progress": agg["in_progress"],
        "cancelled": agg["cancelled"],
        "cod_goods_value": str(agg["cod_value_total"]),
        "cod_expected": str(cod_expected),
        "cod_collected": str(cod_collected),
        "cod_outstanding": str(cod_outstanding),
        "cod_fees_earned": str(cod_fees_earned.quantize(Decimal("0.01"))),
        "delivery_rate": _pct(delivered, agg["total_orders"]),
        "cod_fee_config": {"flat": str(flat), "pct": str(pct)},
        "source": {"cod_fees_earned": "estimated", "cod_collected": "actual"},
    }

    top_riders = [
        {
            "rider_id": r["rider__rider_id"],
            "name": r["rider__user__contact_name"],
            "orders": r["orders"],
            "cod_amount": str(r["cod"]),
        }
        for r in (
            cod_qs.filter(status__in=DELIVERED_STATUSES, rider__isnull=False)
            .values("rider__rider_id", "rider__user__contact_name")
            .annotate(orders=Count("id"), cod=Coalesce(Sum("cod_amount"), ZERO))
            .order_by("-cod")[:10]
        )
    ]

    top_merchants = [
        {
            "merchant": m["user__business_name"],
            "orders": m["orders"],
            "cod_amount": str(m["cod"]),
        }
        for m in (
            cod_qs.filter(status__in=DELIVERED_STATUSES)
            .values("user__business_name")
            .annotate(orders=Count("id"), cod=Coalesce(Sum("cod_amount"), ZERO))
            .order_by("-cod")[:10]
        )
    ]

    return {
        "cards": cards,
        "ageing": _ageing(cod_qs),
        "top_riders": top_riders,
        "top_merchants": top_merchants,
    }
