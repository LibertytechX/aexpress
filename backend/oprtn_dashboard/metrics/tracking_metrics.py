"""
TrackingMetrics — live rider & vehicle (VehicleAsset) tracking.

This is a **live snapshot** (current state), not a date-filtered report:
  - Rider tracking: status (online/on_delivery/offline), is_moving, GPS coords,
    speed, last_location_update, and a derived `gps_status` (moving/idle/offline).
  - Vehicle tracking: engine_status, speed, last_telemetry_at, and a derived
    `tracking_status` (moving/idle/offline).
  - Linkage: each Rider links to its `vehicle_asset`; the live list joins both so
    you can see a rider together with their vehicle's telemetry.

GPS status logic mirrors the guide §4 (offline if no recent ping ≥ 2h).
"""

from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

STALE_MINUTES = 120  # no ping for ≥2h ⇒ offline


def rider_gps_status(rider, now, cutoff):
    if rider.is_moving:
        return "moving"
    if rider.last_location_update and rider.last_location_update >= cutoff:
        return "idle"
    if rider.status == "online" and rider.current_latitude is not None:
        return "idle"
    return "offline"


def vehicle_tracking_status(va, cutoff):
    if not va.last_telemetry_at or va.last_telemetry_at < cutoff:
        return "offline"
    if (va.speed or 0) > 0:
        return "moving"
    return "idle"


def tracking_dashboard(limit=50):
    from dispatcher.models import Rider, VehicleAsset

    now = timezone.now()
    cutoff = now - timedelta(minutes=STALE_MINUTES)

    # ── Rider counts (one aggregate) ────────────────────────────────
    riders_agg = Rider.objects.aggregate(
        total=Count("id"),
        online=Count("id", filter=Q(status="online")),
        on_delivery=Count("id", filter=Q(status="on_delivery")),
        offline=Count("id", filter=Q(status="offline")),
        moving_now=Count("id", filter=Q(is_moving=True)),
        gps_tracked=Count("id", filter=Q(current_latitude__isnull=False)),
    )

    # ── Vehicle counts (one aggregate) ──────────────────────────────
    veh_agg = VehicleAsset.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        moving_now=Count("id", filter=Q(speed__gt=0)),
        with_telemetry=Count("id", filter=Q(last_telemetry_at__isnull=False)),
        stale=Count("id", filter=Q(last_telemetry_at__lt=cutoff)),
        never_reported=Count("id", filter=Q(last_telemetry_at__isnull=True)),
        engine_on=Count("id", filter=Q(engine_status="on")),
        engine_off=Count("id", filter=Q(engine_status="off")),
        engine_idle=Count("id", filter=Q(engine_status="idle")),
        engine_unknown=Count("id", filter=Q(engine_status="unknown")),
        assigned=Count("id", filter=Q(riders__isnull=False)),
    )

    # ── Live linked list (riders with GPS, joined to their vehicle) ──
    live = []
    riders = (
        Rider.objects.filter(current_latitude__isnull=False)
        .select_related("user", "vehicle_asset")
        .order_by("-last_location_update")[:limit]
    )
    moving = idle = offline = 0
    for r in riders:
        gps = rider_gps_status(r, now, cutoff)
        if gps == "moving":
            moving += 1
        elif gps == "idle":
            idle += 1
        else:
            offline += 1
        va = r.vehicle_asset
        live.append({
            "rider_id": r.rider_id,
            "name": r.user.contact_name or r.user.get_full_name(),
            "rider_status": r.status,
            "gps_status": gps,
            "is_moving": r.is_moving,
            "latitude": float(r.current_latitude) if r.current_latitude is not None else None,
            "longitude": float(r.current_longitude) if r.current_longitude is not None else None,
            "speed": float(r.current_speed or 0),
            "last_location_update": (
                r.last_location_update.isoformat() if r.last_location_update else None
            ),
            "vehicle": None if not va else {
                "asset_id": va.asset_id,
                "plate_number": va.plate_number,
                "vehicle_type": va.vehicle_type,
                "engine_status": va.engine_status,
                "tracking_status": vehicle_tracking_status(va, cutoff),
                "speed": float(va.speed or 0),
                "last_telemetry_at": (
                    va.last_telemetry_at.isoformat() if va.last_telemetry_at else None
                ),
            },
        })

    return {
        "as_of": now.isoformat(),
        "riders": {
            **riders_agg,
            "by_gps_status": {"moving": moving, "idle": idle, "offline": offline},
        },
        "vehicles": {
            "total": veh_agg["total"],
            "active": veh_agg["active"],
            "assigned_to_rider": veh_agg["assigned"],
            "moving_now": veh_agg["moving_now"],
            "with_telemetry": veh_agg["with_telemetry"],
            "offline": veh_agg["stale"] + veh_agg["never_reported"],
            "by_engine_status": {
                "on": veh_agg["engine_on"],
                "off": veh_agg["engine_off"],
                "idle": veh_agg["engine_idle"],
                "unknown": veh_agg["engine_unknown"],
            },
        },
        "live": live,
    }
