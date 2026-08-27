"""
Alert rule evaluators.

Each evaluator takes its ``AlertRule`` (for thresholds/params) and returns the
**current firing set** as a list of candidate dicts. The engine (engine.py)
reconciles that set against open alerts — creating new ones, refreshing existing
ones, and auto-resolving those whose condition has cleared. Evaluators therefore
only answer "what is firing right now?"; they never write to the DB.

Candidate dict shape:
    {
        "alert_type", "dedupe_key", "severity", "entity_type",
        "title", "description", "value" (Decimal|None), "context" (dict),
        "rider"|"order"|"merchant"|"vehicle"|"zone": instance (optional),
    }

Phase 4 implements BIKE_AFTER_HOURS and INCOMPLETE_ORDER. Remaining types are
registered as they are built; unregistered types are skipped by the engine.
"""

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from oprtn_dashboard.models import AlertType, Severity


def _in_curfew(local_hour, start_hour, end_hour):
    """True if local_hour is within an overnight curfew window (e.g. 20→06)."""
    if start_hour <= end_hour:
        return start_hour <= local_hour < end_hour
    # window crosses midnight (e.g. 20:00 .. 06:00)
    return local_hour >= start_hour or local_hour < end_hour


def evaluate_bike_after_hours(rule):
    """Bikes moving during the overnight curfew (default 20:00–06:00)."""
    from dispatcher.models import VehicleAsset

    params = rule.params or {}
    start_hour = int(params.get("curfew_start_hour", 20))
    end_hour = int(params.get("curfew_end_hour", 6))
    vehicle_types = params.get("vehicle_types", ["bike"])
    min_speed = Decimal(str(params.get("min_speed_kmh", 5)))
    # Only consider fresh telemetry so we flag movement happening *now*.
    freshness = max(int(rule.window_minutes or 15), 5)

    now = timezone.now()
    cutoff = now - timedelta(minutes=freshness)

    qs = (
        VehicleAsset.objects.filter(
            vehicle_type__in=vehicle_types,
            speed__gt=min_speed,
            last_telemetry_at__isnull=False,
            last_telemetry_at__gte=cutoff,
        )
        .prefetch_related("riders")
    )

    candidates = []
    for va in qs:
        local = timezone.localtime(va.last_telemetry_at)
        if not _in_curfew(local.hour, start_hour, end_hour):
            continue

        rider = va.riders.first()
        local_date = timezone.localdate(va.last_telemetry_at)
        candidates.append(
            {
                "alert_type": AlertType.BIKE_AFTER_HOURS,
                "dedupe_key": f"BIKE_AFTER_HOURS:{va.id}:{local_date}",
                "severity": rule.default_severity or Severity.HIGH,
                "entity_type": "vehicle",
                "vehicle": va,
                "rider": rider,
                "title": f"Bike {va.plate_number} moving after hours",
                "description": (
                    f"{va.speed} km/h at {local:%H:%M} "
                    f"(curfew {start_hour:02d}:00–{end_hour:02d}:00)."
                ),
                "value": Decimal(str(va.speed or 0)),
                "context": {
                    "plate_number": va.plate_number,
                    "speed_kmh": str(va.speed),
                    "local_time": local.isoformat(),
                    "rider_id": rider.rider_id if rider else None,
                },
            }
        )
    return candidates


def evaluate_incomplete_order(rule):
    """Orders a rider accepted but never completed within the window."""
    from orders.models import Order

    params = rule.params or {}
    accepted_statuses = params.get(
        "accepted_statuses",
        ["AssignmentAccepted", "Started", "Pickup", "Fulfilling", "Arrived"],
    )
    window = int(rule.window_minutes or 360)

    now = timezone.now()
    cutoff = now - timedelta(minutes=window)

    qs = (
        Order.objects.filter(
            status__in=accepted_statuses,
            assigned_at__isnull=False,
            assigned_at__lte=cutoff,
        )
        .select_related("rider", "rider__user")
    )

    candidates = []
    for order in qs:
        hours = Decimal(
            str(round((now - order.assigned_at).total_seconds() / 3600, 2))
        )
        candidates.append(
            {
                "alert_type": AlertType.INCOMPLETE_ORDER,
                "dedupe_key": f"INCOMPLETE_ORDER:{order.id}",
                "severity": rule.default_severity or Severity.HIGH,
                "entity_type": "order",
                "order": order,
                "rider": order.rider,
                "title": f"Order {order.order_number} not completed",
                "description": (
                    f"Status '{order.status}' for {hours}h since assignment "
                    f"(threshold {window // 60}h)."
                ),
                "value": hours,
                "context": {
                    "order_number": order.order_number,
                    "status": order.status,
                    "assigned_at": order.assigned_at.isoformat(),
                    "hours_since_assigned": str(hours),
                },
            }
        )
    return candidates


def _tier_severity(value, critical_threshold, base):
    """CRITICAL if value crosses critical_threshold, else the base severity."""
    if critical_threshold is not None and value >= critical_threshold:
        return Severity.CRITICAL
    return base


def evaluate_ghost_ride(rule):
    """Rider offline but their assigned vehicle is moving."""
    from dispatcher.models import Rider

    params = rule.params or {}
    min_speed = Decimal(str(params.get("min_speed_kmh", 5)))
    freshness = max(int(rule.window_minutes or 15), 5)
    now = timezone.now()
    cutoff = now - timedelta(minutes=freshness)

    qs = Rider.objects.filter(
        status="offline",
        vehicle_asset__isnull=False,
        vehicle_asset__speed__gt=min_speed,
        vehicle_asset__last_telemetry_at__gte=cutoff,
    ).select_related("user", "vehicle_asset")

    candidates = []
    for r in qs:
        va = r.vehicle_asset
        candidates.append(
            {
                "alert_type": AlertType.GHOST_RIDE,
                "dedupe_key": f"GHOST_RIDE:{r.id}:{timezone.localdate()}",
                "severity": rule.default_severity or Severity.CRITICAL,
                "entity_type": "rider",
                "rider": r,
                "vehicle": va,
                "title": f"Ghost ride — {r.rider_id} offline but moving",
                "description": (
                    f"Rider offline while {va.plate_number} moves at "
                    f"{va.speed} km/h."
                ),
                "value": Decimal(str(va.speed or 0)),
                "context": {
                    "rider_id": r.rider_id,
                    "plate_number": va.plate_number,
                    "speed_kmh": str(va.speed),
                },
            }
        )
    return candidates


def evaluate_speed_violation(rule):
    """Vehicle speed over the warning / critical thresholds."""
    from dispatcher.models import VehicleAsset

    warn = rule.warn_threshold or Decimal("80")
    crit = rule.critical_threshold
    freshness = max(int(rule.window_minutes or 15), 5)
    now = timezone.now()
    cutoff = now - timedelta(minutes=freshness)

    qs = VehicleAsset.objects.filter(
        speed__gte=warn, last_telemetry_at__gte=cutoff
    ).prefetch_related("riders")

    candidates = []
    for va in qs:
        speed = Decimal(str(va.speed or 0))
        severity = _tier_severity(
            speed, crit, rule.default_severity or Severity.HIGH
        )
        rider = va.riders.first()
        candidates.append(
            {
                "alert_type": AlertType.SPEED_VIOLATION,
                "dedupe_key": f"SPEED_VIOLATION:{va.id}:{timezone.localdate()}",
                "severity": severity,
                "entity_type": "vehicle",
                "vehicle": va,
                "rider": rider,
                "title": f"Speeding — {va.plate_number} at {speed} km/h",
                "description": f"Speed {speed} km/h (warn {warn}, crit {crit}).",
                "value": speed,
                "context": {
                    "plate_number": va.plate_number,
                    "speed_kmh": str(speed),
                },
            }
        )
    return candidates


def evaluate_gps_offline(rule):
    """Active vehicle with no telemetry for longer than the window."""
    from dispatcher.models import VehicleAsset

    window = int(rule.window_minutes or 120)
    now = timezone.now()
    cutoff = now - timedelta(minutes=window)

    qs = VehicleAsset.objects.filter(
        is_active=True,
        last_telemetry_at__isnull=False,
        last_telemetry_at__lte=cutoff,
    ).prefetch_related("riders")

    candidates = []
    for va in qs:
        minutes = Decimal(
            str(round((now - va.last_telemetry_at).total_seconds() / 60))
        )
        rider = va.riders.first()
        candidates.append(
            {
                "alert_type": AlertType.GPS_OFFLINE,
                "dedupe_key": f"GPS_OFFLINE:{va.id}",
                "severity": rule.default_severity or Severity.MEDIUM,
                "entity_type": "vehicle",
                "vehicle": va,
                "rider": rider,
                "title": f"GPS offline — {va.plate_number}",
                "description": f"No telemetry for {minutes} min.",
                "value": minutes,
                "context": {
                    "plate_number": va.plate_number,
                    "last_telemetry_at": va.last_telemetry_at.isoformat(),
                },
            }
        )
    return candidates


def evaluate_sync_failure(rule):
    """Telemetry sync returned a non-2xx response for a vehicle."""
    from dispatcher.models import VehicleAsset

    qs = VehicleAsset.objects.filter(sync_meta__isnull=False).exclude(
        sync_meta={}
    )

    candidates = []
    for va in qs:
        code = (va.sync_meta or {}).get("response_code")
        try:
            code_int = int(code)
        except (TypeError, ValueError):
            continue
        if 200 <= code_int < 300:
            continue
        candidates.append(
            {
                "alert_type": AlertType.SYNC_FAILURE,
                "dedupe_key": f"SYNC_FAILURE:{va.id}",
                "severity": rule.default_severity or Severity.HIGH,
                "entity_type": "vehicle",
                "vehicle": va,
                "title": f"Telemetry sync failed — {va.plate_number}",
                "description": f"Last sync response {code_int}.",
                "value": Decimal(str(code_int)),
                "context": {"plate_number": va.plate_number, "sync_meta": va.sync_meta},
            }
        )
    return candidates


def evaluate_order_stuck(rule):
    """Order never started (Pending/Assigned) past the window."""
    from orders.models import Order

    params = rule.params or {}
    statuses = params.get("statuses", ["Pending", "Assigned"])
    window = int(rule.window_minutes or 240)
    now = timezone.now()
    cutoff = now - timedelta(minutes=window)

    qs = Order.objects.filter(
        status__in=statuses, created_at__lte=cutoff
    ).select_related("rider")

    candidates = []
    for order in qs:
        hours = Decimal(
            str(round((now - order.created_at).total_seconds() / 3600, 2))
        )
        candidates.append(
            {
                "alert_type": AlertType.ORDER_STUCK,
                "dedupe_key": f"ORDER_STUCK:{order.id}",
                "severity": rule.default_severity or Severity.MEDIUM,
                "entity_type": "order",
                "order": order,
                "rider": order.rider,
                "title": f"Order {order.order_number} stuck",
                "description": f"Status '{order.status}' for {hours}h, never started.",
                "value": hours,
                "context": {
                    "order_number": order.order_number,
                    "status": order.status,
                },
            }
        )
    return candidates


def evaluate_order_delayed(rule):
    """In-transit order taking too long since pickup."""
    from orders.models import Order

    params = rule.params or {}
    statuses = params.get(
        "statuses", ["Started", "Pickup", "Fulfilling", "Arrived"]
    )
    window = int(rule.window_minutes or 360)
    now = timezone.now()
    cutoff = now - timedelta(minutes=window)

    qs = Order.objects.filter(
        status__in=statuses,
        picked_up_at__isnull=False,
        picked_up_at__lte=cutoff,
    ).select_related("rider")

    candidates = []
    for order in qs:
        hours = Decimal(
            str(round((now - order.picked_up_at).total_seconds() / 3600, 2))
        )
        candidates.append(
            {
                "alert_type": AlertType.ORDER_DELAYED,
                "dedupe_key": f"ORDER_DELAYED:{order.id}",
                "severity": rule.default_severity or Severity.MEDIUM,
                "entity_type": "order",
                "order": order,
                "rider": order.rider,
                "title": f"Order {order.order_number} delayed in transit",
                "description": f"Status '{order.status}' for {hours}h since pickup.",
                "value": hours,
                "context": {
                    "order_number": order.order_number,
                    "status": order.status,
                },
            }
        )
    return candidates


def evaluate_relay_routing_failure(rule):
    """Relay order whose async routing failed."""
    from orders.models import Order

    qs = Order.objects.filter(
        is_relay_order=True, routing_status="failed"
    ).select_related("rider")

    candidates = []
    for order in qs:
        candidates.append(
            {
                "alert_type": AlertType.RELAY_ROUTING_FAILURE,
                "dedupe_key": f"RELAY_ROUTING_FAILURE:{order.id}",
                "severity": rule.default_severity or Severity.HIGH,
                "entity_type": "order",
                "order": order,
                "rider": order.rider,
                "title": f"Relay routing failed — {order.order_number}",
                "description": (order.routing_error or "Routing failed.")[:240],
                "value": None,
                "context": {
                    "order_number": order.order_number,
                    "routing_error": order.routing_error,
                },
            }
        )
    return candidates


def evaluate_cod_retention(rule):
    """COD collected by a rider but unremitted past the warning window."""
    from riders.models import RiderCodRecord

    params = rule.params or {}
    warn_hours = int(params.get("warn_hours", 24))
    crit_hours = int(params.get("critical_hours", 48))
    now = timezone.now()
    cutoff = now - timedelta(hours=warn_hours)

    qs = RiderCodRecord.objects.filter(
        status="pending", created_at__lte=cutoff
    ).select_related("rider", "rider__user", "order")

    candidates = []
    for rec in qs:
        hours = round((now - rec.created_at).total_seconds() / 3600, 1)
        severity = (
            Severity.CRITICAL
            if hours >= crit_hours
            else (rule.default_severity or Severity.HIGH)
        )
        candidates.append(
            {
                "alert_type": AlertType.COD_RETENTION,
                "dedupe_key": f"COD_RETENTION:{rec.id}",
                "severity": severity,
                "entity_type": "rider",
                "rider": rec.rider,
                "order": rec.order,
                "title": f"COD unremitted — {rec.rider.rider_id}",
                "description": f"₦{rec.amount} pending {hours}h.",
                "value": rec.amount,
                "context": {
                    "rider_id": rec.rider.rider_id,
                    "amount": str(rec.amount),
                    "hours_pending": str(hours),
                },
            }
        )
    return candidates


def _make_expiry_evaluator(field_name, alert_type, label):
    """Build a compliance-document expiry evaluator for one date field."""

    def evaluator(rule):
        from dispatcher.models import VehicleAsset

        params = rule.params or {}
        warn_days = int(params.get("warn_days", 60))
        crit_days = int(params.get("critical_days", 30))
        today = timezone.localdate()
        warn_cutoff = today + timedelta(days=warn_days)

        qs = VehicleAsset.objects.filter(
            **{f"{field_name}__isnull": False, f"{field_name}__lte": warn_cutoff}
        ).prefetch_related("riders")

        candidates = []
        for va in qs:
            expiry = getattr(va, field_name)
            days_until = (expiry - today).days
            severity = (
                Severity.CRITICAL
                if days_until <= crit_days
                else (rule.default_severity or Severity.MEDIUM)
            )
            state = "expired" if days_until < 0 else f"expires in {days_until}d"
            rider = va.riders.first()
            candidates.append(
                {
                    "alert_type": alert_type,
                    "dedupe_key": f"{alert_type}:{va.id}",
                    "severity": severity,
                    "entity_type": "vehicle",
                    "vehicle": va,
                    "rider": rider,
                    "title": f"{va.plate_number} {label} {state}",
                    "description": f"{label} expiry {expiry.isoformat()} ({state}).",
                    "value": Decimal(str(days_until)),
                    "context": {
                        "plate_number": va.plate_number,
                        "expiry": expiry.isoformat(),
                        "days_until": days_until,
                    },
                }
            )
        return candidates

    return evaluator


# ── Rider behaviour (overriding / attendance / output) ──────────────
#
# These evaluators share their computation with the behaviour dashboards
# (metrics/rider_behavior.py) so an alert always matches what the dashboard
# shows for the same window.


def _local_day_window(day=None):
    """Aware (start, end) datetimes spanning one local calendar day."""
    from datetime import datetime, time

    day = day or timezone.localdate()
    start = timezone.make_aware(datetime.combine(day, time.min))
    end = timezone.make_aware(datetime.combine(day, time.max))
    return day, start, end


def _riders_by_pk(pks):
    from dispatcher.models import Rider

    return Rider.objects.select_related("user").in_bulk(list(pks))


def evaluate_overriding(rule):
    """
    Rider whose delivered orders today covered more km than the saved
    estimate + allowance (default 8 km). Value = total overriding km; the
    per-order accumulation is kept in context.
    """
    from oprtn_dashboard.metrics.rider_behavior import (
        DEFAULT_ALLOWANCE_KM,
        overriding_report,
    )

    params = rule.params or {}
    allowance = float(params.get("allowance_km", DEFAULT_ALLOWANCE_KM))
    warn = float(rule.warn_threshold or 0)
    crit = rule.critical_threshold

    day, start, end = _local_day_window()
    report = overriding_report(start, end, allowance_km=allowance)
    offenders = [
        r
        for r in report["riders"]
        if r["total_overriding_km"] > 0 and r["total_overriding_km"] >= warn
    ]
    riders = _riders_by_pk(r["rider_pk"] for r in offenders)

    candidates = []
    for row in offenders:
        rider = riders.get(row["rider_pk"])
        if rider is None:
            continue
        over_km = Decimal(str(row["total_overriding_km"]))
        candidates.append(
            {
                "alert_type": AlertType.OVERRIDING,
                "dedupe_key": f"OVERRIDING:{rider.pk}:{day}",
                "severity": _tier_severity(
                    over_km, crit, rule.default_severity or Severity.HIGH
                ),
                "entity_type": "rider",
                "rider": rider,
                "vehicle": rider.vehicle_asset,
                "title": (
                    f"Overriding — {row['rider_id']} "
                    f"+{row['total_overriding_km']} km over allowance"
                ),
                "description": (
                    f"{row['orders_over']} of {row['orders_checked']} orders "
                    f"exceeded estimate + {allowance:g} km "
                    f"(actual {row['total_actual_km']} km vs allowed "
                    f"{row['total_allowed_km']} km)."
                ),
                "value": over_km,
                "context": {
                    "rider_id": row["rider_id"],
                    "date": day.isoformat(),
                    "allowance_km": allowance,
                    "orders_checked": row["orders_checked"],
                    "orders_over": row["orders_over"],
                    "total_estimated_km": row["total_estimated_km"],
                    "total_allowed_km": row["total_allowed_km"],
                    "total_actual_km": row["total_actual_km"],
                    "total_overriding_km": row["total_overriding_km"],
                    "orders": row["orders"],
                },
            }
        )
    return candidates


def evaluate_rider_offline_moving(rule):
    """
    Attendance breach: the rider's bike moved during the work window
    (default 08:00–22:00) while the rider was offline. Value = offline km.
    """
    from oprtn_dashboard.metrics.rider_behavior import (
        DEFAULT_DAY_END_HOUR,
        DEFAULT_DAY_START_HOUR,
        attendance_report,
    )

    params = rule.params or {}
    day_start = int(params.get("day_start_hour", DEFAULT_DAY_START_HOUR))
    day_end = int(params.get("day_end_hour", DEFAULT_DAY_END_HOUR))
    warn = float(rule.warn_threshold or 2)
    crit = rule.critical_threshold

    day, start, end = _local_day_window()
    report = attendance_report(
        start, end, day_start_hour=day_start, day_end_hour=day_end
    )
    offenders = [
        r for r in report["riders"] if r["offline_moving_km"] >= warn
    ]
    riders = _riders_by_pk(r["rider_pk"] for r in offenders)

    candidates = []
    for row in offenders:
        rider = riders.get(row["rider_pk"])
        if rider is None:
            continue
        offline_km = Decimal(str(row["offline_moving_km"]))
        candidates.append(
            {
                "alert_type": AlertType.RIDER_OFFLINE_MOVING,
                "dedupe_key": f"RIDER_OFFLINE_MOVING:{rider.pk}:{day}",
                "severity": _tier_severity(
                    offline_km, crit, rule.default_severity or Severity.HIGH
                ),
                "entity_type": "rider",
                "rider": rider,
                "vehicle": rider.vehicle_asset,
                "title": (
                    f"Offline but moving — {row['rider_id']} "
                    f"({row['offline_moving_km']} km)"
                ),
                "description": (
                    f"Bike moved {row['offline_moving_km']} km while the "
                    f"rider was offline (online {row['online_minutes']} min, "
                    f"window {day_start:02d}:00–{day_end:02d}:00)."
                ),
                "value": offline_km,
                "context": {
                    "rider_id": row["rider_id"],
                    "date": day.isoformat(),
                    "plate_number": row["plate_number"],
                    "online_minutes": row["online_minutes"],
                    "offline_minutes": row["offline_minutes"],
                    "online_km": row["online_km"],
                    "offline_moving_km": row["offline_moving_km"],
                    "days": row["days"],
                },
            }
        )
    return candidates


def evaluate_low_revenue(rule):
    """Working rider whose net revenue over the window is below threshold."""
    from oprtn_dashboard.metrics.rider_behavior import (
        active_rider_pks,
        revenue_leaderboard,
    )

    warn = rule.warn_threshold
    if warn is None:
        return []
    crit = rule.critical_threshold
    window = int(rule.window_minutes or 1440)
    now = timezone.now()
    start = now - timedelta(minutes=window)

    report = revenue_leaderboard(start, now, top=10_000)
    active = active_rider_pks(start, now)
    by_rider_id = {}
    for row in report["bottom_riders"]:
        if Decimal(row["net_revenue"]) < warn:
            by_rider_id[row["rider_id"]] = row

    from dispatcher.models import Rider

    riders = Rider.objects.select_related("user", "vehicle_asset").filter(
        rider_id__in=by_rider_id.keys(), pk__in=active
    )

    candidates = []
    for rider in riders:
        row = by_rider_id[rider.rider_id]
        net = Decimal(row["net_revenue"])
        severity = (
            Severity.CRITICAL
            if crit is not None and net <= crit
            else (rule.default_severity or Severity.MEDIUM)
        )
        candidates.append(
            {
                "alert_type": AlertType.LOW_REVENUE,
                "dedupe_key": f"LOW_REVENUE:{rider.pk}:{timezone.localdate()}",
                "severity": severity,
                "entity_type": "rider",
                "rider": rider,
                "title": (
                    f"Low revenue — {rider.rider_id} ₦{row['net_revenue']} "
                    f"net in {window // 60}h"
                ),
                "description": (
                    f"{row['delivered']} delivered orders, gross "
                    f"₦{row['gross_revenue']}, net ₦{row['net_revenue']} "
                    f"(threshold ₦{warn})."
                ),
                "value": net,
                "context": {
                    "rider_id": rider.rider_id,
                    "window_minutes": window,
                    "delivered": row["delivered"],
                    "gross_revenue": row["gross_revenue"],
                    "commission": row["commission"],
                    "net_revenue": row["net_revenue"],
                },
            }
        )
    return candidates


def evaluate_low_order_volume(rule):
    """Working rider with fewer delivered orders than threshold in window."""
    from oprtn_dashboard.metrics.rider_behavior import (
        active_rider_pks,
        order_leaderboard,
    )

    warn = rule.warn_threshold
    if warn is None:
        return []
    crit = rule.critical_threshold
    window = int(rule.window_minutes or 1440)
    now = timezone.now()
    start = now - timedelta(minutes=window)

    report = order_leaderboard(start, now, top=10_000)
    active = active_rider_pks(start, now)
    by_rider_id = {
        row["rider_id"]: row
        for row in report["bottom_riders"]
        if row["delivered"] < warn
    }

    from dispatcher.models import Rider

    riders = Rider.objects.select_related("user").filter(
        rider_id__in=by_rider_id.keys(), pk__in=active
    )

    candidates = []
    for rider in riders:
        row = by_rider_id[rider.rider_id]
        delivered = Decimal(row["delivered"])
        severity = (
            Severity.CRITICAL
            if crit is not None and delivered <= crit
            else (rule.default_severity or Severity.MEDIUM)
        )
        candidates.append(
            {
                "alert_type": AlertType.LOW_ORDER_VOLUME,
                "dedupe_key": (
                    f"LOW_ORDER_VOLUME:{rider.pk}:{timezone.localdate()}"
                ),
                "severity": severity,
                "entity_type": "rider",
                "rider": rider,
                "title": (
                    f"Low orders — {rider.rider_id} delivered "
                    f"{row['delivered']} in {window // 60}h"
                ),
                "description": (
                    f"{row['delivered']} delivered orders "
                    f"(threshold {warn}), gross ₦{row['gross_revenue']}."
                ),
                "value": delivered,
                "context": {
                    "rider_id": rider.rider_id,
                    "window_minutes": window,
                    "delivered": row["delivered"],
                    "gross_revenue": row["gross_revenue"],
                },
            }
        )
    return candidates


def evaluate_fuel_misuse(rule):
    """
    Rider collected fuel today but delivered fewer than the minimum orders
    (default 10 of 15 expected). Only evaluated from `evaluate_after_hour`
    local time so riders have had the day to work.
    """
    from oprtn_dashboard.metrics.rider_behavior import fuel_misuse_report

    params = rule.params or {}
    min_orders = int(rule.warn_threshold or params.get("min_orders", 10))
    expected = int(params.get("expected_orders", 15))
    after_hour = int(params.get("evaluate_after_hour", 17))
    crit = rule.critical_threshold

    if timezone.localtime().hour < after_hour:
        return []

    day, start, end = _local_day_window()
    report = fuel_misuse_report(
        start, end, min_orders=min_orders, expected_orders=expected
    )
    riders = _riders_by_pk(r["rider_pk"] for r in report["flagged"])

    candidates = []
    for row in report["flagged"]:
        rider = riders.get(row["rider_pk"])
        if rider is None:
            continue
        delivered = Decimal(row["orders_delivered"])
        severity = (
            Severity.CRITICAL
            if crit is not None and delivered <= crit
            else (rule.default_severity or Severity.HIGH)
        )
        candidates.append(
            {
                "alert_type": AlertType.FUEL_MISUSE,
                "dedupe_key": f"FUEL_MISUSE:{rider.pk}:{row['date']}",
                "severity": severity,
                "entity_type": "rider",
                "rider": rider,
                "vehicle": rider.vehicle_asset,
                "title": (
                    f"Fuel misuse — {row['rider_id']} fueled "
                    f"₦{row['fuel_cost']}, delivered "
                    f"{row['orders_delivered']}/{expected}"
                ),
                "description": (
                    f"Collected {row['liters']} L (₦{row['fuel_cost']}) on "
                    f"{row['date']} but delivered {row['orders_delivered']} "
                    f"orders (minimum {min_orders} of {expected} expected), "
                    f"revenue ₦{row['revenue']}."
                ),
                "value": delivered,
                "context": {
                    "rider_id": row["rider_id"],
                    "date": row["date"],
                    "fuel_cost": row["fuel_cost"],
                    "liters": row["liters"],
                    "orders_delivered": row["orders_delivered"],
                    "orders_expected": expected,
                    "min_orders": min_orders,
                    "revenue": row["revenue"],
                },
            }
        )
    return candidates


evaluate_insurance_expiring = _make_expiry_evaluator(
    "insurance_expiry", AlertType.INSURANCE_EXPIRING, "insurance"
)
evaluate_registration_expiring = _make_expiry_evaluator(
    "registration_expiry", AlertType.REGISTRATION_EXPIRING, "registration"
)
evaluate_roadworthiness_expiring = _make_expiry_evaluator(
    "road_worthiness_expiry", AlertType.ROADWORTHINESS_EXPIRING, "road-worthiness"
)


# Registry: alert_type -> evaluator. Only registered types are evaluated.
RULE_EVALUATORS = {
    AlertType.BIKE_AFTER_HOURS: evaluate_bike_after_hours,
    AlertType.INCOMPLETE_ORDER: evaluate_incomplete_order,
    AlertType.GHOST_RIDE: evaluate_ghost_ride,
    AlertType.SPEED_VIOLATION: evaluate_speed_violation,
    AlertType.GPS_OFFLINE: evaluate_gps_offline,
    AlertType.SYNC_FAILURE: evaluate_sync_failure,
    AlertType.ORDER_STUCK: evaluate_order_stuck,
    AlertType.ORDER_DELAYED: evaluate_order_delayed,
    AlertType.RELAY_ROUTING_FAILURE: evaluate_relay_routing_failure,
    AlertType.COD_RETENTION: evaluate_cod_retention,
    AlertType.OVERRIDING: evaluate_overriding,
    AlertType.RIDER_OFFLINE_MOVING: evaluate_rider_offline_moving,
    AlertType.LOW_REVENUE: evaluate_low_revenue,
    AlertType.LOW_ORDER_VOLUME: evaluate_low_order_volume,
    AlertType.FUEL_MISUSE: evaluate_fuel_misuse,
    AlertType.INSURANCE_EXPIRING: evaluate_insurance_expiring,
    AlertType.REGISTRATION_EXPIRING: evaluate_registration_expiring,
    AlertType.ROADWORTHINESS_EXPIRING: evaluate_roadworthiness_expiring,
}
