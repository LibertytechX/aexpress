"""
FuelMetrics — fuel-spend stats from imported `FuelBill` rows.

`fuel_dashboard(qs)` takes a date-filtered FuelBill queryset (filtered on
`bill_date`) and returns spend/efficiency totals plus breakdowns by vehicle,
rider, station, fuel type, and a daily trend.
"""

from decimal import Decimal

from django.db.models import Avg, Count, Sum
from django.db.models.functions import Coalesce

ZERO = Decimal("0")


def _dec(v):
    return str(v if v is not None else ZERO)


def fuel_dashboard(qs):
    agg = qs.aggregate(
        records=Count("id"),
        total_cost=Coalesce(Sum("cost"), ZERO),
        total_liters=Coalesce(Sum("liters"), ZERO),
        total_tip=Coalesce(Sum("worker_tip"), ZERO),
        avg_fuel_price=Avg("fuel_price"),
        avg_km_per_l=Avg("km_per_l"),
    )

    by_vehicle = [
        {
            "vehicle_plate": r["vehicle_plate"],
            "records": r["records"],
            "cost": _dec(r["cost"]),
            "liters": _dec(r["liters"]),
        }
        for r in (
            qs.values("vehicle_plate")
            .annotate(
                records=Count("id"),
                cost=Coalesce(Sum("cost"), ZERO),
                liters=Coalesce(Sum("liters"), ZERO),
            )
            .order_by("-cost")[:10]
        )
    ]

    by_rider = [
        {
            "rider_id": r["rider__rider_id"],
            "name": r["rider__user__contact_name"],
            "records": r["records"],
            "cost": _dec(r["cost"]),
            "liters": _dec(r["liters"]),
        }
        for r in (
            qs.filter(rider__isnull=False)
            .values("rider__rider_id", "rider__user__contact_name")
            .annotate(
                records=Count("id"),
                cost=Coalesce(Sum("cost"), ZERO),
                liters=Coalesce(Sum("liters"), ZERO),
            )
            .order_by("-cost")[:10]
        )
    ]

    by_station = [
        {"station": r["station"], "records": r["records"], "cost": _dec(r["cost"])}
        for r in (
            qs.values("station")
            .annotate(records=Count("id"), cost=Coalesce(Sum("cost"), ZERO))
            .order_by("-cost")[:10]
        )
    ]

    by_fuel_type = [
        {
            "fuel_type": r["fuel_type"],
            "records": r["records"],
            "cost": _dec(r["cost"]),
            "liters": _dec(r["liters"]),
        }
        for r in (
            qs.values("fuel_type")
            .annotate(
                records=Count("id"),
                cost=Coalesce(Sum("cost"), ZERO),
                liters=Coalesce(Sum("liters"), ZERO),
            )
            .order_by("-cost")
        )
    ]

    daily_trend = [
        {
            "date": r["bill_date"].isoformat(),
            "cost": _dec(r["cost"]),
            "liters": _dec(r["liters"]),
            "records": r["records"],
        }
        for r in (
            qs.values("bill_date")
            .annotate(
                records=Count("id"),
                cost=Coalesce(Sum("cost"), ZERO),
                liters=Coalesce(Sum("liters"), ZERO),
            )
            .order_by("bill_date")
        )
    ]

    avg_price = agg["avg_fuel_price"]
    avg_kmpl = agg["avg_km_per_l"]
    return {
        "summary": {
            "records": agg["records"],
            "total_cost": _dec(agg["total_cost"]),
            "total_liters": _dec(agg["total_liters"]),
            "total_worker_tip": _dec(agg["total_tip"]),
            "avg_fuel_price": str(round(avg_price, 2)) if avg_price else "0",
            "avg_km_per_l": str(round(avg_kmpl, 2)) if avg_kmpl else "0",
            "source": "actual",
        },
        "by_vehicle": by_vehicle,
        "by_rider": by_rider,
        "by_station": by_station,
        "by_fuel_type": by_fuel_type,
        "daily_trend": daily_trend,
    }
