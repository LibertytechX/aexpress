"""
RiderBehavior metrics — overriding, attendance, revenue/order leaderboards,
and fuel misuse. Shared by the behaviour dashboards (views.py) and the alert
evaluators (alerts/rules.py) so both always agree on the numbers.

Definitions:
  - Overriding: for each delivered order, actual km covered (odometer delta
    from `dispatcher.VehicleTracking` between pickup and completion) minus the
    allowed km (Order.distance_km estimate + a fixed allowance, default 8 km).
    Anything above the allowance is "overriding km", accumulated per rider
    with a per-order breakdown.
  - Attendance: per rider per day, minutes online vs offline inside the work
    window (default 08:00–22:00, from `RiderDutyLog` sessions), plus the km
    the rider's bike moved while they were online vs offline. Offline movement
    is flagged as `riders_offline_moving`.
  - Leaderboards: riders ranked by net revenue (gross minus commission) and
    by delivered-order volume — top and bottom N.
  - Fuel misuse: riders who collected fuel on a day (FuelBill) but delivered
    fewer than `min_orders` orders that day.

All report functions take timezone-aware (start_dt, end_dt) from
`filters.parse_filter`, so every endpoint honours the general dashboard filter.
"""

from bisect import bisect_left, bisect_right
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from .order_metrics import DELIVERED_STATUSES, _commission_pct

ZERO = Decimal("0")

DEFAULT_ALLOWANCE_KM = 8.0
DEFAULT_DAY_START_HOUR = 8
DEFAULT_DAY_END_HOUR = 22
MAX_ATTENDANCE_DAYS = 31


def _aware(dt):
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def _km(value):
    return round(float(value or 0), 2)


def _money(value):
    value = value if value is not None else ZERO
    return str(value.quantize(Decimal("0.01")))


def _rider_name(user):
    return (user.contact_name or "").strip() or str(user)


# ── VehicleTracking odometer helpers ─────────────────────────────────


def _tracking_by_vehicle(vehicle_ids, start_dt, end_dt):
    """{vehicle_id: [(created_at, travelled_km), ...] sorted by time}."""
    from dispatcher.models import VehicleTracking

    points = {}
    rows = (
        VehicleTracking.objects.filter(
            vehicle_asset_id__in=list(vehicle_ids),
            created_at__gte=start_dt,
            created_at__lte=end_dt,
            travelled__isnull=False,
        )
        .order_by("created_at")
        .values_list("vehicle_asset_id", "created_at", "travelled")
    )
    for vid, ts, travelled in rows:
        points.setdefault(vid, []).append((ts, float(travelled)))
    return points


def _odometer_km(points, start, end):
    """
    Odometer delta between the first and last snapshot inside [start, end].
    Returns None when there are no usable snapshots (vehicle untracked).
    """
    if not points or start is None or end is None or start > end:
        return None
    times = [p[0] for p in points]
    lo = bisect_left(times, start)
    hi = bisect_right(times, end) - 1
    if lo > hi:
        return None
    return max(0.0, points[hi][1] - points[lo][1])


def _split_distance(points, window_start, window_end, online_intervals):
    """
    Split the km moved inside [window_start, window_end] into (online_km,
    offline_km) using the tracking snapshots. Each consecutive-snapshot
    segment's km is attributed by its midpoint: inside an online interval →
    online, otherwise offline.
    """
    online_km = offline_km = 0.0
    if not points:
        return online_km, offline_km
    times = [p[0] for p in points]
    lo = bisect_left(times, window_start)
    hi = bisect_right(times, window_end)
    window_points = points[lo:hi]
    for (t1, km1), (t2, km2) in zip(window_points, window_points[1:]):
        delta = max(0.0, km2 - km1)
        if not delta:
            continue
        midpoint = t1 + (t2 - t1) / 2
        if any(s <= midpoint < e for s, e in online_intervals):
            online_km += delta
        else:
            offline_km += delta
    return online_km, offline_km


def _merge_intervals(intervals):
    """Merge overlapping (start, end) tuples; drop empty ones."""
    merged = []
    for start, end in sorted(i for i in intervals if i[0] < i[1]):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


# ── Overriding ────────────────────────────────────────────────────────


def _order_start(order):
    return order.picked_up_at or order.assigned_at or order.created_at


def overriding_report(
    start_dt,
    end_dt,
    *,
    allowance_km=DEFAULT_ALLOWANCE_KM,
    top=10,
    orders_detail_cap=25,
):
    """
    Per-rider overriding km for delivered orders completed inside the window,
    with the per-order breakdown of how each rider's total accumulated.
    """
    from orders.models import Order

    allowance = float(allowance_km)
    orders = list(
        Order.objects.filter(
            status__in=DELIVERED_STATUSES,
            rider__isnull=False,
            completed_at__gte=start_dt,
            completed_at__lte=end_dt,
        )
        .select_related("rider", "rider__user", "rider__vehicle_asset")
        .order_by("completed_at")
    )

    vehicle_ids = {
        o.rider.vehicle_asset_id for o in orders if o.rider.vehicle_asset_id
    }
    earliest = min((_order_start(o) for o in orders), default=start_dt)
    points = _tracking_by_vehicle(vehicle_ids, earliest, end_dt)

    riders = {}
    checked = no_estimate = untracked = orders_over = 0
    for order in orders:
        rider = order.rider
        estimated = float(order.distance_km) if order.distance_km else None
        actual = None
        if rider.vehicle_asset_id:
            actual = _odometer_km(
                points.get(rider.vehicle_asset_id, []),
                _order_start(order),
                order.completed_at,
            )
        if estimated is None:
            no_estimate += 1
            continue
        if actual is None:
            untracked += 1
            continue

        checked += 1
        allowed = estimated + allowance
        overriding = max(0.0, actual - allowed)
        if overriding:
            orders_over += 1

        entry = riders.setdefault(
            rider.pk,
            {
                "rider_pk": rider.pk,
                "rider_id": rider.rider_id,
                "name": _rider_name(rider.user),
                "plate_number": (
                    rider.vehicle_asset.plate_number
                    if rider.vehicle_asset
                    else None
                ),
                "orders_checked": 0,
                "orders_over": 0,
                "total_estimated_km": 0.0,
                "total_allowed_km": 0.0,
                "total_actual_km": 0.0,
                "total_overriding_km": 0.0,
                "orders": [],
            },
        )
        entry["orders_checked"] += 1
        entry["orders_over"] += 1 if overriding else 0
        entry["total_estimated_km"] += estimated
        entry["total_allowed_km"] += allowed
        entry["total_actual_km"] += actual
        entry["total_overriding_km"] += overriding
        if len(entry["orders"]) < orders_detail_cap:
            entry["orders"].append(
                {
                    "order_number": order.order_number,
                    "completed_at": order.completed_at.isoformat(),
                    "estimated_km": _km(estimated),
                    "allowed_km": _km(allowed),
                    "actual_km": _km(actual),
                    "overriding_km": _km(overriding),
                }
            )

    rider_rows = sorted(
        riders.values(), key=lambda r: -r["total_overriding_km"]
    )
    for row in rider_rows:
        for field in (
            "total_estimated_km",
            "total_allowed_km",
            "total_actual_km",
            "total_overriding_km",
        ):
            row[field] = _km(row[field])

    offenders = [r for r in rider_rows if r["total_overriding_km"] > 0]
    return {
        "summary": {
            "allowance_km": allowance,
            "orders_delivered": len(orders),
            "orders_checked": checked,
            "orders_no_estimate": no_estimate,
            "orders_untracked": untracked,
            "orders_with_overriding": orders_over,
            "riders_with_overriding": len(offenders),
            "total_overriding_km": _km(
                sum(r["total_overriding_km"] for r in offenders)
            ),
        },
        "riders": rider_rows,
        "top_riders": offenders[:top],
    }


# ── Attendance (online/offline vs bike movement, 08:00–22:00) ────────


def attendance_report(
    start_dt,
    end_dt,
    *,
    day_start_hour=DEFAULT_DAY_START_HOUR,
    day_end_hour=DEFAULT_DAY_END_HOUR,
    top=10,
    max_days=MAX_ATTENDANCE_DAYS,
):
    """
    Per-rider daily attendance inside the work window: minutes online vs
    offline (RiderDutyLog) against the km their bike moved while online vs
    offline (VehicleTracking). Offline movement = `riders_offline_moving`.
    """
    from dispatcher.models import Rider, RiderDutyLog

    first_day = timezone.localtime(start_dt).date()
    last_day = timezone.localtime(end_dt).date()
    n_days = (last_day - first_day).days + 1
    truncated = n_days > max_days
    if truncated:  # keep the most recent max_days of the requested range
        first_day = last_day - timedelta(days=max_days - 1)
        n_days = max_days
    days = [first_day + timedelta(days=i) for i in range(n_days)]

    range_start = _aware(datetime.combine(first_day, time(day_start_hour)))
    range_end = _aware(datetime.combine(last_day, time(day_end_hour)))

    duty_by_rider = {}
    duty_rows = RiderDutyLog.objects.filter(
        went_online__lte=range_end
    ).filter(
        Q(went_offline__gte=range_start) | Q(went_offline__isnull=True)
    ).values_list("rider_id", "went_online", "went_offline")
    for rider_pk, on, off in duty_rows:
        duty_by_rider.setdefault(rider_pk, []).append((on, off))

    riders = [
        r
        for r in Rider.objects.filter(is_active=True).select_related(
            "user", "vehicle_asset"
        )
        if r.vehicle_asset_id or r.pk in duty_by_rider
    ]
    points = _tracking_by_vehicle(
        {r.vehicle_asset_id for r in riders if r.vehicle_asset_id},
        range_start,
        range_end,
    )

    window_minutes = (day_end_hour - day_start_hour) * 60
    rider_rows = []
    for rider in riders:
        sessions = duty_by_rider.get(rider.pk, [])
        vehicle_points = points.get(rider.vehicle_asset_id, [])
        totals = {
            "online_minutes": 0,
            "offline_minutes": 0,
            "online_km": 0.0,
            "offline_moving_km": 0.0,
        }
        day_rows = []
        for day in days:
            ws = _aware(datetime.combine(day, time(day_start_hour)))
            we = _aware(datetime.combine(day, time(day_end_hour)))
            online = _merge_intervals(
                [
                    (max(on, ws), min(off or we, we))
                    for on, off in sessions
                    if on <= we and (off is None or off >= ws)
                ]
            )
            online_min = round(
                sum((e - s).total_seconds() for s, e in online) / 60
            )
            online_km, offline_km = _split_distance(
                vehicle_points, ws, we, online
            )
            totals["online_minutes"] += online_min
            totals["offline_minutes"] += window_minutes - online_min
            totals["online_km"] += online_km
            totals["offline_moving_km"] += offline_km
            if online_min or online_km or offline_km:
                day_rows.append(
                    {
                        "date": day.isoformat(),
                        "online_minutes": online_min,
                        "offline_minutes": window_minutes - online_min,
                        "online_km": _km(online_km),
                        "offline_moving_km": _km(offline_km),
                    }
                )

        rider_rows.append(
            {
                "rider_pk": rider.pk,
                "rider_id": rider.rider_id,
                "name": _rider_name(rider.user),
                "plate_number": (
                    rider.vehicle_asset.plate_number
                    if rider.vehicle_asset
                    else None
                ),
                "status": rider.status,
                "online_minutes": totals["online_minutes"],
                "offline_minutes": totals["offline_minutes"],
                "online_km": _km(totals["online_km"]),
                "offline_moving_km": _km(totals["offline_moving_km"]),
                "riders_offline_moving": totals["offline_moving_km"] > 0,
                "days": day_rows,
            }
        )

    rider_rows.sort(key=lambda r: -r["offline_moving_km"])
    offenders = [r for r in rider_rows if r["offline_moving_km"] > 0]
    return {
        "summary": {
            "work_window": f"{day_start_hour:02d}:00–{day_end_hour:02d}:00",
            "days": n_days,
            "days_truncated": truncated,
            "riders": len(rider_rows),
            "riders_offline_moving": len(offenders),
            "total_offline_moving_km": _km(
                sum(r["offline_moving_km"] for r in offenders)
            ),
        },
        "riders": rider_rows,
        "top_offline_moving": offenders[:top],
    }


# ── Revenue / order leaderboards ─────────────────────────────────────


def _delivered_by_rider(start_dt, end_dt):
    from orders.models import Order

    return (
        Order.objects.filter(
            status__in=DELIVERED_STATUSES,
            rider__isnull=False,
            completed_at__gte=start_dt,
            completed_at__lte=end_dt,
        )
        .values("rider__pk", "rider__rider_id", "rider__user__contact_name")
        .annotate(
            delivered=Count("id"),
            revenue=Coalesce(Sum("total_amount"), ZERO),
        )
    )


def _zero_rider_rows(seen_pks):
    """Active riders with no delivered orders in the window (revenue 0)."""
    from dispatcher.models import Rider

    return [
        {
            "rider_pk": pk,
            "rider_id": rider_id,
            "name": (contact_name or "").strip() or rider_id,
            "delivered": 0,
            "revenue": ZERO,
        }
        for pk, rider_id, contact_name in Rider.objects.filter(is_active=True)
        .exclude(pk__in=seen_pks)
        .values_list("pk", "rider_id", "user__contact_name")
    ]


def revenue_leaderboard(start_dt, end_dt, *, top=20):
    """
    Riders ranked by net revenue (gross delivered revenue minus their
    commission) — top N earners and bottom N (including zero-revenue riders).
    """
    pct = _commission_pct()
    rows = []
    for r in _delivered_by_rider(start_dt, end_dt):
        rows.append(
            {
                "rider_pk": r["rider__pk"],
                "rider_id": r["rider__rider_id"],
                "name": (r["rider__user__contact_name"] or "").strip()
                or r["rider__rider_id"],
                "delivered": r["delivered"],
                "revenue": r["revenue"],
            }
        )
    all_rows = rows + _zero_rider_rows({r["rider_pk"] for r in rows})

    def serialize(r):
        commission = r["revenue"] * pct / Decimal("100")
        return {
            "rider_id": r["rider_id"],
            "name": r["name"],
            "delivered": r["delivered"],
            "gross_revenue": _money(r["revenue"]),
            "commission": _money(commission),
            "net_revenue": _money(r["revenue"] - commission),
        }

    for r in all_rows:
        r["net"] = r["revenue"] * (Decimal("100") - pct) / Decimal("100")
    earners = sorted(rows, key=lambda r: -r["net"])
    lowest = sorted(all_rows, key=lambda r: (r["net"], r["delivered"]))

    gross_total = sum((r["revenue"] for r in rows), ZERO)
    commission_total = gross_total * pct / Decimal("100")
    return {
        "summary": {
            "riders_with_revenue": len(rows),
            "riders_total": len(all_rows),
            "gross_revenue": _money(gross_total),
            "commission_total": _money(commission_total),
            "net_revenue": _money(gross_total - commission_total),
            "commission_pct": str(pct),
        },
        "top_riders": [serialize(r) for r in earners[:top]],
        "bottom_riders": [serialize(r) for r in lowest[:top]],
    }


def order_leaderboard(start_dt, end_dt, *, top=20):
    """Riders ranked by delivered-order volume — lowest N (and top N)."""
    rows = [
        {
            "rider_pk": r["rider__pk"],
            "rider_id": r["rider__rider_id"],
            "name": (r["rider__user__contact_name"] or "").strip()
            or r["rider__rider_id"],
            "delivered": r["delivered"],
            "revenue": r["revenue"],
        }
        for r in _delivered_by_rider(start_dt, end_dt)
    ]
    all_rows = rows + _zero_rider_rows({r["rider_pk"] for r in rows})

    def serialize(r):
        return {
            "rider_id": r["rider_id"],
            "name": r["name"],
            "delivered": r["delivered"],
            "gross_revenue": _money(r["revenue"]),
        }

    most = sorted(rows, key=lambda r: -r["delivered"])
    fewest = sorted(all_rows, key=lambda r: (r["delivered"], r["revenue"]))
    return {
        "summary": {
            "riders_with_orders": len(rows),
            "riders_total": len(all_rows),
            "orders_delivered": sum(r["delivered"] for r in rows),
        },
        "top_riders": [serialize(r) for r in most[:top]],
        "bottom_riders": [serialize(r) for r in fewest[:top]],
    }


def active_rider_pks(start_dt, end_dt):
    """
    Riders considered "working" in the window: had a duty session overlap,
    any order assigned, or a fuel bill. Used so low-revenue / low-order
    alerts don't fire for riders who simply weren't rostered.
    """
    from dispatcher.models import RiderDutyLog
    from orders.models import Order

    from oprtn_dashboard.models import FuelBill

    active = set(
        RiderDutyLog.objects.filter(went_online__lte=end_dt)
        .filter(Q(went_offline__gte=start_dt) | Q(went_offline__isnull=True))
        .values_list("rider_id", flat=True)
    )
    active.update(
        Order.objects.filter(
            rider__isnull=False,
            created_at__gte=start_dt,
            created_at__lte=end_dt,
        ).values_list("rider_id", flat=True)
    )
    active.update(
        FuelBill.objects.filter(
            rider__isnull=False,
            bill_date__gte=timezone.localtime(start_dt).date(),
            bill_date__lte=timezone.localtime(end_dt).date(),
        ).values_list("rider_id", flat=True)
    )
    return active


# ── Fuel misuse ──────────────────────────────────────────────────────


def fuel_misuse_report(
    start_dt, end_dt, *, min_orders=10, expected_orders=15
):
    """
    Riders who collected fuel on a day (FuelBill) but delivered fewer than
    `min_orders` orders (of `expected_orders` expected) that day — i.e. fuel
    spend without matching output/revenue.
    """
    from orders.models import Order

    from oprtn_dashboard.models import FuelBill

    first_day = timezone.localtime(start_dt).date()
    last_day = timezone.localtime(end_dt).date()

    bills = list(
        FuelBill.objects.filter(
            rider__isnull=False,
            bill_date__gte=first_day,
            bill_date__lte=last_day,
        )
        .values(
            "rider__pk",
            "rider__rider_id",
            "rider__user__contact_name",
            "bill_date",
        )
        .annotate(
            bills=Count("id"),
            fuel_cost=Coalesce(Sum("cost"), ZERO),
            liters=Coalesce(Sum("liters"), ZERO),
        )
    )

    delivered = {}
    if bills:
        rider_pks = {b["rider__pk"] for b in bills}
        for row in (
            Order.objects.filter(
                status__in=DELIVERED_STATUSES,
                rider__pk__in=rider_pks,
                completed_at__gte=start_dt,
                completed_at__lte=end_dt,
            )
            .annotate(day=TruncDate("completed_at"))
            .values("rider__pk", "day")
            .annotate(
                orders=Count("id"),
                revenue=Coalesce(Sum("total_amount"), ZERO),
            )
        ):
            delivered[(row["rider__pk"], row["day"])] = row

    rows = []
    for b in bills:
        done = delivered.get((b["rider__pk"], b["bill_date"]), {})
        orders_done = done.get("orders", 0)
        revenue = done.get("revenue", ZERO)
        rows.append(
            {
                "rider_pk": b["rider__pk"],
                "rider_id": b["rider__rider_id"],
                "name": (b["rider__user__contact_name"] or "").strip()
                or b["rider__rider_id"],
                "date": b["bill_date"].isoformat(),
                "fuel_bills": b["bills"],
                "fuel_cost": _money(b["fuel_cost"]),
                "liters": str(b["liters"]),
                "orders_delivered": orders_done,
                "orders_expected": expected_orders,
                "min_orders": min_orders,
                "revenue": _money(revenue),
                "flagged": orders_done < min_orders,
            }
        )
    rows.sort(
        key=lambda r: (not r["flagged"], r["orders_delivered"], r["date"])
    )
    flagged = [r for r in rows if r["flagged"]]

    return {
        "summary": {
            "min_orders": min_orders,
            "expected_orders": expected_orders,
            "fuel_days": len(rows),
            "flagged_days": len(flagged),
            "riders_fueled": len({r["rider_pk"] for r in rows}),
            "riders_flagged": len({r["rider_pk"] for r in flagged}),
            "flagged_fuel_cost": _money(
                sum((Decimal(r["fuel_cost"]) for r in flagged), ZERO)
            ),
        },
        "rows": rows,
        "flagged": flagged,
    }
