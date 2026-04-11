import os
import logging
import time
import math
import secrets
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

import requests
from celery import shared_task
from django.conf import settings
from django.db.models import Count, Q, Sum
from django.utils import timezone

from .models import Rider
from .utils import MailgunEmailService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# OCC Snapshot & Maintenance Tasks
# ---------------------------------------------------------------------------


@shared_task
def aggregate_daily_rider_snapshots(target_date=None):
    """
    Nightly task: aggregate yesterday's metrics per rider into RiderDailySnapshot.
    Scheduled at 00:05 Africa/Lagos.
    """
    from orders.models import Order
    from .models import RiderDailySnapshot, RiderDutyLog

    if target_date is None:
        target_date = date.today() - timedelta(days=1)
    elif isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    day_start = timezone.make_aware(
        timezone.datetime.combine(target_date, timezone.datetime.min.time())
    )
    day_end = day_start + timedelta(days=1)

    riders = Rider.objects.all()
    created_count = 0

    for rider in riders.iterator():
        rider_orders = Order.objects.filter(
            rider=rider,
            created_at__gte=day_start,
            created_at__lt=day_end,
        )
        completed = rider_orders.filter(status="Done").count()
        rejected = rider_orders.filter(
            status__in=["CustomerCanceled", "RiderCanceled"]
        ).count()
        failed = rider_orders.filter(status="Failed").count()
        revenue = rider_orders.filter(status="Done").aggregate(
            total=Sum("total_amount")
        )["total"] or Decimal("0")
        distance = rider_orders.filter(status="Done").aggregate(
            total=Sum("distance_km")
        )["total"] or Decimal("0")

        # Online minutes from RiderDutyLog
        duty_logs = RiderDutyLog.objects.filter(
            rider=rider,
            went_online__lt=day_end,
        ).filter(Q(went_offline__gte=day_start) | Q(went_offline__isnull=True))

        online_mins = 0
        peak_mins = 0
        for log in duty_logs:
            start = max(log.went_online, day_start)
            end = min(log.went_offline or day_end, day_end)
            if end > start:
                online_mins += int((end - start).total_seconds() / 60)

            # Peak hours: 12-15 and 17-20
            for peak_start_h, peak_end_h in [(12, 15), (17, 20)]:
                peak_s = day_start.replace(hour=peak_start_h, minute=0, second=0)
                peak_e = day_start.replace(hour=peak_end_h, minute=0, second=0)
                overlap_start = max(start, peak_s)
                overlap_end = min(end, peak_e)
                if overlap_end > overlap_start:
                    peak_mins += int((overlap_end - overlap_start).total_seconds() / 60)

        RiderDailySnapshot.objects.update_or_create(
            rider=rider,
            date=target_date,
            defaults={
                "orders_completed": completed,
                "orders_rejected": rejected,
                "orders_failed": failed,
                "revenue": revenue,
                "distance_km": distance,
                "online_minutes": online_mins,
                "peak_hour_minutes": peak_mins,
                "ghost_ride_minutes": 0,  # populated by flag_ghost_riders
            },
        )
        created_count += 1

    logger.info(
        f"aggregate_daily_rider_snapshots: {created_count} snapshots for {target_date}"
    )
    return created_count


@shared_task
def aggregate_daily_merchant_snapshots(target_date=None):
    """
    Nightly task: aggregate yesterday's metrics per merchant into MerchantDailySnapshot.
    Scheduled at 00:10 Africa/Lagos.
    """
    from orders.models import Order
    from .models import Merchant, MerchantDailySnapshot

    if target_date is None:
        target_date = date.today() - timedelta(days=1)
    elif isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    day_start = timezone.make_aware(
        timezone.datetime.combine(target_date, timezone.datetime.min.time())
    )
    day_end = day_start + timedelta(days=1)

    merchants = Merchant.objects.select_related("user").all()
    created_count = 0

    for merchant in merchants.iterator():
        merchant_orders = Order.objects.filter(
            user=merchant.user,
            created_at__gte=day_start,
            created_at__lt=day_end,
        )
        placed = merchant_orders.count()
        completed = merchant_orders.filter(status="Done").count()
        failed = merchant_orders.filter(status="Failed").count()
        revenue = merchant_orders.filter(status="Done").aggregate(
            total=Sum("total_amount")
        )["total"] or Decimal("0")

        MerchantDailySnapshot.objects.update_or_create(
            merchant=merchant.user,
            date=target_date,
            defaults={
                "orders_placed": placed,
                "orders_completed": completed,
                "orders_failed": failed,
                "revenue": revenue,
            },
        )
        created_count += 1

    logger.info(
        f"aggregate_daily_merchant_snapshots: {created_count} snapshots for {target_date}"
    )
    return created_count


@shared_task
def update_merchant_activity_status():
    """
    Every 6 hours: update Merchant.activity_status based on order frequency.
    - active: ordered within last 7 days
    - watch: ordered within last 30 days (but not last 7)
    - inactive: no order in 30+ days
    """
    from .models import Merchant

    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # Active: last_order_date within 7 days
    active_count = (
        Merchant.objects.filter(last_order_date__gte=seven_days_ago)
        .exclude(activity_status="active")
        .update(activity_status="active")
    )

    # Watch: last_order_date between 7-30 days
    watch_count = (
        Merchant.objects.filter(
            last_order_date__lt=seven_days_ago,
            last_order_date__gte=thirty_days_ago,
        )
        .exclude(activity_status="watch")
        .update(activity_status="watch")
    )

    # Inactive: last_order_date > 30 days or null
    inactive_count = (
        Merchant.objects.filter(
            Q(last_order_date__lt=thirty_days_ago) | Q(last_order_date__isnull=True)
        )
        .exclude(activity_status="inactive")
        .update(activity_status="inactive")
    )

    logger.info(
        f"update_merchant_activity_status: active={active_count}, "
        f"watch={watch_count}, inactive={inactive_count}"
    )
    return {"active": active_count, "watch": watch_count, "inactive": inactive_count}


@shared_task
def flag_ghost_riders():
    """
    Every 15 minutes: detect riders who are offline but whose current_speed > 5 km/h.
    Logs a warning and increments their daily ghost_ride_minutes.
    """
    from .models import RiderDailySnapshot

    today = date.today()
    ghost_riders = Rider.objects.filter(
        status=Rider.Status.OFFLINE,
        current_speed__gt=5,
    )

    flagged = 0
    for rider in ghost_riders:
        logger.warning(
            f"Ghost rider detected: {rider.rider_id} "
            f"(speed={rider.current_speed} km/h, status={rider.status})"
        )
        # Add 15 minutes to today's ghost_ride_minutes
        snapshot, _ = RiderDailySnapshot.objects.get_or_create(
            rider=rider,
            date=today,
            defaults={
                "orders_completed": 0,
                "orders_rejected": 0,
                "orders_failed": 0,
                "revenue": Decimal("0"),
                "distance_km": Decimal("0"),
                "online_minutes": 0,
                "peak_hour_minutes": 0,
                "ghost_ride_minutes": 0,
            },
        )
        snapshot.ghost_ride_minutes += 15
        snapshot.save(update_fields=["ghost_ride_minutes"])
        flagged += 1

    if flagged:
        logger.info(f"flag_ghost_riders: {flagged} ghost riders flagged")
    return flagged


_RELAY_NODES_CACHE = {"ts": 0.0, "nodes": None}
_RELAY_NODES_TTL_SECONDS = 300


def _haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance in KM."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _get_active_relay_nodes_cached():
    from .models import RelayNode

    now = time.time()
    if (
        _RELAY_NODES_CACHE["nodes"] is not None
        and (now - _RELAY_NODES_CACHE["ts"]) < _RELAY_NODES_TTL_SECONDS
    ):
        return _RELAY_NODES_CACHE["nodes"]

    nodes = list(
        RelayNode.objects.filter(is_active=True)
        .select_related("zone")
        .only("id", "name", "latitude", "longitude", "zone")
    )
    _RELAY_NODES_CACHE["nodes"] = nodes
    _RELAY_NODES_CACHE["ts"] = now
    return nodes


def _directions_legs(origin, points):
    """Return list of (distance_km, duration_minutes) between origin->points[0]->..."""
    api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
    if not api_key:
        return None

    if not points:
        return []

    all_points = [origin] + points
    origins = all_points[:-1]
    targets = all_points[1:]

    origins_str = "|".join([f"{p['lat']},{p['lng']}" for p in origins])
    destinations_str = "|".join([f"{p['lat']},{p['lng']}" for p in targets])

    params = {
        "origins": origins_str,
        "destinations": destinations_str,
        "key": api_key,
    }

    # 1-hour cache for identical waypoint chains
    try:
        from django.core.cache import cache

        cache_key = "relay_route_legs:" + "->".join(
            [f"{origin['lat']},{origin['lng']}"]
            + [f"{p['lat']},{p['lng']}" for p in points]
        )
        cached = cache.get(cache_key)
        if cached:
            return cached
    except Exception:
        cache_key = None

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "OK":
        return None

    out = []
    for i in range(len(origins)):
        try:
            elements = data["rows"][i]["elements"]
            element = elements[i]
            if element.get("status") == "OK":
                d_km = (element["distance"]["value"] or 0) / 1000.0
                t_min = int(round((element["duration"]["value"] or 0) / 60.0))
                out.append((round(d_km, 2), t_min))
            else:
                return None
        except (IndexError, KeyError):
            return None

    if cache_key:
        try:
            from django.core.cache import cache

            cache.set(cache_key, out, timeout=3600)
        except Exception:
            pass

    return out


def _estimate_legs_haversine(origin, points):
    if not points:
        return []
    prev = origin
    out = []
    for p in points:
        d = _haversine_km(prev["lat"], prev["lng"], p["lat"], p["lng"])
        # simple Lagos ETA heuristic: 4 mins per km
        out.append((round(d, 2), int(max(1, round(d * 4)))))
        prev = p
    return out


def _route_distance_km(origin, destination):
    """Best-effort route distance in KM for a single origin/destination pair."""
    try:
        legs = _directions_legs(origin, [destination])
    except Exception as exc:
        logger.warning(f"_route_distance_km directions lookup failed: {exc}")
        legs = None

    if legs:
        return float(legs[0][0] or 0.0)

    return _haversine_km(
        origin["lat"], origin["lng"], destination["lat"], destination["lng"]
    )


MAX_RELAY_LEG_KM = 10.0
RELAY_LEG_DISTANCE_EPSILON_KM = 0.01
RELAY_THRESHOLD_KM = MAX_RELAY_LEG_KM


def _nearest_rider_to(lat, lng, hub=None):
    """Return the nearest authorized rider (with GPS) to (lat, lng)."""
    filters = {
        "is_authorized": True,
        "current_latitude__isnull": False,
        "current_longitude__isnull": False,
    }
    if hub:
        filters["hub"] = hub

    riders = Rider.objects.filter(**filters)
    best, best_d = None, None
    for r in riders[:200]:
        d = _haversine_km(
            lat, lng, float(r.current_latitude), float(r.current_longitude)
        )
        if best is None or d < best_d:
            best, best_d = r, d
    return best


def _point_along_line(start, end, distance_km):
    """Return an approximate point `distance_km` from start toward end."""
    total = _haversine_km(start["lat"], start["lng"], end["lat"], end["lng"])
    if total <= 0:
        return {"lat": start["lat"], "lng": start["lng"]}

    fraction = max(0.0, min(1.0, distance_km / total))
    return {
        "lat": start["lat"] + ((end["lat"] - start["lat"]) * fraction),
        "lng": start["lng"] + ((end["lng"] - start["lng"]) * fraction),
    }


def _build_greedy_relay_hops(pickup, dropoff, max_leg_km_est=MAX_RELAY_LEG_KM):
    """
    Build a continuous relay-node chain from pickup to dropoff.

    At each step:
    - stop once the dropoff is directly reachable within `max_leg_km_est`;
    - prefer unused relay nodes whose route distance from the current point is
      within `max_leg_km_est` and that move closer to the dropoff;
    - among those, choose the node with the shortest remaining route distance
      to the destination, then the one closest to the ideal ~`max_leg_km_est`
      target;
    - if none exist, fall back to the nearest unused relay node that still
      improves progress toward the destination;
    - fail if no forward progress is possible.
    """
    nodes = _get_active_relay_nodes_cached()
    direct_route_km = _route_distance_km(pickup, dropoff)

    if direct_route_km <= max_leg_km_est:
        return []

    available_nodes = [
        n for n in nodes if n.latitude is not None and n.longitude is not None
    ]

    hops = []
    cur = pickup
    remaining_route_km = direct_route_km
    used_node_ids = set()

    while remaining_route_km > (max_leg_km_est + RELAY_LEG_DISTANCE_EPSILON_KM):
        target = _point_along_line(cur, dropoff, max_leg_km_est)
        strict_candidates = []
        fallback_candidates = []

        for n in available_nodes:
            if n.id in used_node_ids:
                continue

            n_lat, n_lng = float(n.latitude), float(n.longitude)
            node_point = {"lat": n_lat, "lng": n_lng}
            leg_route_km = _route_distance_km(cur, node_point)
            if leg_route_km <= 0:
                continue

            remaining_from_node_km = _route_distance_km(node_point, dropoff)

            # Only consider nodes that move the route closer to the destination.
            if remaining_from_node_km >= (
                remaining_route_km - RELAY_LEG_DISTANCE_EPSILON_KM
            ):
                continue

            target_gap = _haversine_km(target["lat"], target["lng"], n_lat, n_lng)
            tie_breaker = str(n.id)

            candidate = {
                "node": n,
                "leg_km": leg_route_km,
                "remaining_km": remaining_from_node_km,
                "target_gap": target_gap,
                "tie_breaker": tie_breaker,
            }

            if leg_route_km <= (max_leg_km_est + RELAY_LEG_DISTANCE_EPSILON_KM):
                strict_candidates.append(candidate)
                continue

            fallback_candidates.append(candidate)

        best = None
        best_remaining = None
        if strict_candidates:
            best_candidate = min(
                strict_candidates,
                key=lambda c: (
                    c["remaining_km"],
                    c["target_gap"],
                    abs(max_leg_km_est - c["leg_km"]),
                    c["tie_breaker"],
                ),
            )
            best = best_candidate["node"]
            best_remaining = best_candidate["remaining_km"]
        elif fallback_candidates:
            best_candidate = min(
                fallback_candidates,
                key=lambda c: (
                    c["leg_km"],
                    c["remaining_km"],
                    c["target_gap"],
                    c["tie_breaker"],
                ),
            )
            best = best_candidate["node"]
            best_remaining = best_candidate["remaining_km"]

        if not best or best_remaining is None:
            return None

        if best_remaining >= (remaining_route_km - RELAY_LEG_DISTANCE_EPSILON_KM):
            return None

        hops.append(best)
        used_node_ids.add(best.id)
        cur = {"lat": float(best.latitude), "lng": float(best.longitude)}
        remaining_route_km = best_remaining

    return hops


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="dispatcher.tasks.notify_relay_vertical_leads",
)
def notify_relay_vertical_leads(self, parent_order_number, sub_order_ids):
    """
    Send an SMS to each vertical lead whose riders were assigned relay legs.

    Groups assigned riders by their home-zone vertical lead so each lead
    receives a single, consolidated SMS rather than one per rider.

    Args:
        parent_order_number: Human-readable ID of the parent relay order.
        sub_order_ids:       List of UUID strings for the created sub-orders.
    """
    from authentication.services import send_sms
    from orders.models import Order
    from .models import VerticalLead

    if not sub_order_ids:
        logger.info("notify_relay_vertical_leads: no sub-orders provided, skipping.")
        return

    # Fetch sub-orders with their assigned riders and hubs in one query.
    sub_orders = (
        Order.objects.filter(id__in=sub_order_ids)
        .select_related(
            "rider",
            "rider__user",
            "rider__hub",
            "rider__hub__zone",
            "rider__hub__zone__vertical",
            "rider__hub__zone__vertical__lead",
            "rider__hub__zone__vertical__lead__user",
        )
        .order_by("relay_leg_number")
    )

    # Build mappings for Vertical Leads and Hub Captains
    # Key: (phone, name)  — avoids loading the full object into a dict key
    lead_legs: dict[tuple, list[str]] = {}
    captain_legs: dict[tuple, list[str]] = {}

    for sub in sub_orders:
        rider = sub.rider
        if not rider:
            continue

        hub = rider.hub
        rider_name = (
            rider.user.contact_name
            if (rider.user and rider.user.contact_name)
            else rider.rider_id
        )
        leg_summary = (
            f"Leg {sub.relay_leg_number}: {rider_name} ({rider.rider_id}) — "
            f"pickup: {sub.pickup_address}"
        )

        # 1. Collect data for Vertical Lead
        zone = hub.zone if hub else None
        if zone and zone.vertical:
            try:
                vl = zone.zone_lead
                if vl and vl.is_active:
                    lead_phone = vl.user.phone
                    lead_name = (
                        vl.user.contact_name or vl.user.get_full_name() or "Lead"
                    )
                    key = (lead_phone, lead_name)
                    lead_legs.setdefault(key, []).append(leg_summary)
            except VerticalLead.DoesNotExist:
                pass

        # 2. Collect data for Hub Captain
        if hub and hub.hub_captain_phone:
            captain_phone = hub.hub_captain_phone
            captain_name = hub.hub_captain_name or "Captain"
            c_key = (captain_phone, captain_name)
            captain_legs.setdefault(c_key, []).append(leg_summary)

    if not lead_legs and not captain_legs:
        logger.info(
            "notify_relay_vertical_leads: no eligible leads or captains found, no SMS sent."
        )
        return

    sent = 0
    failed = 0

    # Send consolidated SMS to Vertical Leads
    for (phone, name), legs in lead_legs.items():
        legs_text = "\n".join(f"  • {lg}" for lg in legs)
        message = (
            f"AX Relay Alert — Order #{parent_order_number}\n"
            f"Hi {name}, {len(legs)} rider(s) from your vertical have been assigned:\n"
            f"{legs_text}\n"
            f"Please ensure your riders are ready for pickup."
        )
        if send_sms(phone, message):
            sent += 1
            logger.info(
                f"notify_relay_vertical_leads: SMS sent to vertical lead {name} ({phone})"
            )
        else:
            failed += 1
            logger.error(
                f"notify_relay_vertical_leads: SMS FAILED for vertical lead {name} ({phone})"
            )

    # Send consolidated SMS to Hub Captains
    for (phone, name), legs in captain_legs.items():
        legs_text = "\n".join(f"  • {lg}" for lg in legs)
        message = (
            f"AX Relay Alert — Order #{parent_order_number}\n"
            f"Hi {name}, {len(legs)} rider(s) from your hub have been assigned relay leg(s):\n"
            f"{legs_text}\n"
            f"Please ensure your riders are ready."
        )
        if send_sms(phone, message):
            sent += 1
            logger.info(
                f"notify_relay_vertical_leads: SMS sent to hub captain {name} ({phone})"
            )
        else:
            failed += 1
            logger.error(
                f"notify_relay_vertical_leads: SMS FAILED for hub captain {name} ({phone})"
            )

    logger.info(
        f"notify_relay_vertical_leads: done for order #{parent_order_number} — "
        f"{sent} sent, {failed} failed."
    )


@shared_task
def send_onboarding_email_task(email, first_name, password, rider_id=None):
    """
    Background task to send onboarding email.
    """
    try:
        # Send onboarding email
        MailgunEmailService.send_onboarding_email(email, first_name, password)

        if rider_id:
            logger.info(f"Onboarding email sent for rider {rider_id}")
        else:
            logger.info(f"Onboarding email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Error in send_onboarding_email_task: {str(e)}")
        return False


@shared_task
def export_orders_history_task(user_id, start_date_str, end_date_str):
    """
    Asynchronous task to export order history for a specific date range and email it to the dispatcher.
    """
    import csv
    import io
    from .models import VerticalLead, RelayNode
    from authentication.models import User
    from orders.models import Order

    try:
        user = User.objects.get(id=user_id)
        role = getattr(user.dispatcher_profile, "role", None)

        qs = (
            Order.objects.filter(
                created_at__date__gte=start_date_str, created_at__date__lte=end_date_str
            )
            .select_related("user", "rider", "vehicle")
            .prefetch_related("deliveries")
            .order_by("-created_at")
        )

        # Role-based filtering (logic from OrderViewSet)
        if role == "zone_lead":
            try:
                zone_lead = VerticalLead.objects.get(user=user)
                zones = zone_lead.area_zones.all()
                relay_nodes = RelayNode.objects.filter(zone__in=zones)
                qs = qs.filter(
                    Q(status="Pending")
                    | Q(rider__hub__in=relay_nodes)
                    | Q(legs__start_relay_node__in=relay_nodes)
                    | Q(legs__end_relay_node__in=relay_nodes)
                ).distinct()
            except VerticalLead.DoesNotExist:
                pass

        # Helper for time formatting
        def _format_td(td):
            if not td:
                return ""
            minutes = int(td.total_seconds() / 60)
            if minutes < 60:
                return f"{minutes} mins"
            else:
                hours = minutes // 60
                mins = minutes % 60
                return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Order ID",
                "Date",
                "Customer",
                "Phone",
                "Merchant",
                "Pickup",
                "Dropoff",
                "Rider ID",
                "Rider Name",
                "Vertical Lead Name",
                "Vehicle",
                "Amount",
                "Status",
                "Payment Status",
                "COD Amount",
                "Wait Time",
                "Delivery Time",
                "Total Time",
            ]
        )

        for o in qs:
            first_del = o.deliveries.first()
            customer_name = first_del.receiver_name if first_del else "Unknown"
            customer_phone = first_del.receiver_phone if first_del else ""
            dropoff_address = (
                first_del.dropoff_address if first_del else o.pickup_address
            )  # Fallback

            rider_name = (
                o.rider.user.full_name
                if (o.rider and getattr(o.rider, "user", None))
                else "Unassigned"
            )

            wait_time = (
                _format_td(o.assigned_at - o.created_at)
                if (getattr(o, "assigned_at", None) and o.created_at)
                else ""
            )
            delivery_time = (
                _format_td(o.completed_at - o.assigned_at)
                if (
                    getattr(o, "completed_at", None) and getattr(o, "assigned_at", None)
                )
                else ""
            )
            total_time = (
                _format_td(o.completed_at - o.created_at)
                if (getattr(o, "completed_at", None) and o.created_at)
                else ""
            )

            writer.writerow(
                [
                    o.order_number,
                    o.created_at.strftime("%Y-%m-%d %H:%M"),
                    customer_name,
                    customer_phone,
                    o.user.contact_name if (o.user and o.user.contact_name) else "N/A",
                    o.pickup_address,
                    dropoff_address,
                    o.rider.rider_id if o.rider else "Unassigned",
                    rider_name,
                    o.vertical_lead_name,
                    o.vehicle.name if o.vehicle else "Bike",
                    o.total_amount,
                    o.status,
                    o.payment_status or "Pending",
                    o.cod_amount if o.collect_on_delivery else 0,
                    wait_time,
                    delivery_time,
                    total_time,
                ]
            )

        csv_content = output.getvalue()
        filename = f"orders_export_{start_date_str}_to_{end_date_str}.csv"
        subject = f"Your Requested Order Export ({start_date_str} to {end_date_str})"
        body = f"Hello {user.contact_name or user.first_name or 'Dispatcher'},\n\nPlease find attached the order history export you requested from the AX Dispatcher Portal."

        from .utils import MailgunEmailService

        success = MailgunEmailService.send_csv_attachment_email(
            user.email, csv_content, filename, subject, body
        )

        if success:
            logger.info(f"Export task successful for user {user.id}")
        else:
            logger.error(f"Export task failed to send email for user {user.id}")

    except Exception as e:
        logger.error(f"Error in export_orders_history_task: {str(e)}")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def upload_rider_documents_to_s3(
    self,
    rider_id,
    avatar_data=None,
    avatar_name=None,
    vehicle_photo_data=None,
    vehicle_photo_name=None,
    driving_license_photo_data=None,
    driving_license_photo_name=None,
    identity_card_photo_data=None,
    identity_card_photo_name=None,
):
    """
    Background task to upload rider documents to S3.
    """
    import base64
    import io
    from .s3_utils import upload_image_file_to_s3

    try:
        rider = Rider.objects.get(id=rider_id)

        # Upload Avatar
        if avatar_data and avatar_name:
            file_content = base64.b64decode(avatar_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(file_obj, avatar_name, "riders/avatars")
            if url:
                rider.avatar = url

        # Upload Vehicle Photo
        if vehicle_photo_data and vehicle_photo_name:
            file_content = base64.b64decode(vehicle_photo_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(
                file_obj, vehicle_photo_name, "riders/vehicles"
            )
            if url:
                rider.vehicle_photo = url

        # Upload License
        if driving_license_photo_data and driving_license_photo_name:
            file_content = base64.b64decode(driving_license_photo_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(
                file_obj, driving_license_photo_name, "riders/license"
            )
            if url:
                rider.driving_license_photo = url

        # Upload ID Card
        if identity_card_photo_data and identity_card_photo_name:
            file_content = base64.b64decode(identity_card_photo_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(
                file_obj, identity_card_photo_name, "riders/id_card"
            )
            if url:
                rider.identity_card_photo = url

        rider.save()
        logger.info(f"Successfully uploaded documents for rider {rider_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to upload documents for rider {rider_id}: {str(e)}")
        return False


def generate_relay_legs_sync(order_id):
    """Generate relay legs synchronously for a relay order (called directly by the view)."""
    from django.db import transaction
    from orders.models import Order, OrderLeg
    from orders.utils import geocode_address
    from .utils import emit_activity

    try:
        with transaction.atomic():
            order = (
                Order.objects.select_for_update(of=("self",))
                .prefetch_related("deliveries")
                .get(id=order_id)
            )

            if not order.is_relay_order:
                return True

            first_delivery = order.deliveries.first()
            if not first_delivery:
                order.routing_status = Order.RoutingStatus.FAILED
                order.routing_error = "No delivery dropoff found for this order."
                order.save(update_fields=["routing_status", "routing_error"])
                return False

            # Coordinates (prefer provided lat/lng; fallback to geocode)
            pickup = {
                "lat": order.pickup_latitude,
                "lng": order.pickup_longitude,
            }
            if pickup["lat"] is None or pickup["lng"] is None:
                try:
                    g = geocode_address(order.pickup_address)
                except Exception:
                    g = None
                if not g:
                    order.routing_status = Order.RoutingStatus.FAILED
                    order.routing_error = (
                        "Pickup coordinates missing and geocoding failed."
                    )
                    order.save(update_fields=["routing_status", "routing_error"])
                    return False
                pickup = g
                order.pickup_latitude = pickup["lat"]
                order.pickup_longitude = pickup["lng"]

            dropoff = {
                "lat": first_delivery.dropoff_latitude,
                "lng": first_delivery.dropoff_longitude,
            }
            if dropoff["lat"] is None or dropoff["lng"] is None:
                try:
                    g = geocode_address(first_delivery.dropoff_address)
                except Exception:
                    g = None
                if not g:
                    order.routing_status = Order.RoutingStatus.FAILED
                    order.routing_error = (
                        "Dropoff coordinates missing and geocoding failed."
                    )
                    order.save(update_fields=["routing_status", "routing_error"])
                    return False
                dropoff = g
                first_delivery.dropoff_latitude = dropoff["lat"]
                first_delivery.dropoff_longitude = dropoff["lng"]

            # Build a continuous chain that prefers ~20km relay spacing.
            # Orders within the cap go direct (single leg, no hub handoffs).
            # Longer routes use relay hubs, falling back to the closest forward
            # hub when no hub is available within the preferred cap.
            direct_km = _route_distance_km(pickup, dropoff)
            if direct_km <= RELAY_THRESHOLD_KM:
                hop_nodes = []
            else:
                hop_nodes = _build_greedy_relay_hops(
                    pickup, dropoff, max_leg_km_est=MAX_RELAY_LEG_KM
                )

            if hop_nodes is None:
                order.routing_status = Order.RoutingStatus.FAILED
                order.routing_error = (
                    "Could not find a continuous relay-hub chain for this route."
                )
                order.save(update_fields=["routing_status", "routing_error"])
                emit_activity(
                    event_type="relay_route_failed",
                    order_id=order.order_number,
                    text=f"Relay routing failed for {order.order_number}",
                    color="red",
                    metadata={"reason": order.routing_error},
                )
                return False

            # Points for routing legs: hop coords + final dropoff
            points = [
                {"lat": float(n.latitude), "lng": float(n.longitude)} for n in hop_nodes
            ] + [dropoff]

            legs_metrics = None
            try:
                legs_metrics = _directions_legs(pickup, points)
            except Exception as exc:
                logger.warning(f"generate_relay_legs_task: directions failed: {exc}")

            if legs_metrics is None:
                legs_metrics = _estimate_legs_haversine(pickup, points)

            # Clear and recreate legs (idempotent retries)
            order.legs.all().delete()

            created_legs = []
            prev_node = None
            for idx, (dist_km, dur_min) in enumerate(legs_metrics, start=1):
                print("Regenerating Legs!!!")
                next_node = hop_nodes[idx - 1] if idx - 1 < len(hop_nodes) else None

                # Determine this leg's start coordinates for rider suggestion:
                #   Leg 1  → order pickup point
                #   Leg N  → the hub where the previous leg ended
                if prev_node is None:
                    start_lat = float(pickup["lat"])
                    start_lng = float(pickup["lng"])
                else:
                    start_lat = float(prev_node.latitude)
                    start_lng = float(prev_node.longitude)

                try:
                    suggested = None
                    if prev_node:
                        suggested = _nearest_rider_to(
                            start_lat, start_lng, hub=prev_node
                        )
                    if not suggested:
                        suggested = _nearest_rider_to(start_lat, start_lng)
                except Exception:
                    suggested = None

                leg = OrderLeg.objects.create(
                    order=order,
                    leg_number=idx,
                    start_relay_node=prev_node,
                    end_relay_node=next_node,
                    suggested_rider=suggested,
                    hub_pin=f"{secrets.randbelow(1000000):06d}",
                    distance_km=float(dist_km or 0),
                    duration_minutes=int(dur_min or 0),
                )
                created_legs.append(leg)
                prev_node = next_node

            # Settlement: each leg earns a proportional share of the full
            # order total_amount based on its distance fraction.
            # Formula: leg_payout = (leg_km / total_km) * total_amount
            len_legs = len(created_legs)
            print("Legs generated completed! ", len_legs)
            total_distance = sum(float(l.distance_km or 0) for l in created_legs) or 0.0
            order_total = order.total_amount or Decimal("0")
            if total_distance > 0:
                for leg in created_legs:
                    share = Decimal(str(float(leg.distance_km or 0) / total_distance))
                    payout = (order_total * share).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    leg.rider_payout = payout
                    leg.save(update_fields=["rider_payout"])

            # Keep order.suggested_rider pointing to the leg-1 suggestion
            # (used by the banner; consistent with previous behaviour)
            order.suggested_rider = (
                created_legs[0].suggested_rider if created_legs else None
            )

            # Persist computed totals + status
            order.relay_legs_count = len(created_legs)
            order.distance_km = round(sum(d for d, _ in legs_metrics), 2)
            order.duration_minutes = int(sum(t for _, t in legs_metrics))
            order.routing_status = Order.RoutingStatus.READY
            order.routing_error = ""
            order.save(
                update_fields=[
                    "pickup_latitude",
                    "pickup_longitude",
                    "relay_legs_count",
                    "distance_km",
                    "duration_minutes",
                    "routing_status",
                    "routing_error",
                    "suggested_rider",
                ]
            )
            first_delivery.save(update_fields=["dropoff_latitude", "dropoff_longitude"])

        emit_activity(
            event_type="relay_route_ready",
            order_id=order.order_number,
            text=f"Relay route ready for {order.order_number} ({order.relay_legs_count} legs)",
            color="green",
            metadata={
                "legs": order.relay_legs_count,
                "suggested_rider_id": (
                    str(order.suggested_rider.id) if order.suggested_rider else None
                ),
            },
        )
        return True

    except Exception as exc:
        logger.exception(f"generate_relay_legs_sync failed for order {order_id}: {exc}")
        try:
            from orders.models import Order
            from .utils import emit_activity

            Order.objects.filter(id=order_id).update(
                routing_status=Order.RoutingStatus.FAILED,
                routing_error=str(exc),
            )
            order = Order.objects.filter(id=order_id).first()
            if order:
                emit_activity(
                    event_type="relay_route_failed",
                    order_id=order.order_number,
                    text=f"Relay routing failed for {order.order_number}",
                    color="red",
                    metadata={"error": str(exc)},
                )
        except Exception:
            pass
        return False


@shared_task
def assign_rider_to_sub_order_task(sub_order_id, leg_id, rider_id=None):
    """
    Background task to assign a rider to a sub-order and relay leg,
    and send the corresponding notification.
    """
    from django.utils import timezone
    from orders.models import Order, OrderLeg
    from riders.notifications import notify_rider
    from riders.views import publish_order_assigned_event
    from dispatcher.models import Rider
    import logging

    logger = logging.getLogger(__name__)

    try:
        sub_order = Order.objects.select_related("parent_order").get(id=sub_order_id)
        leg = OrderLeg.objects.get(id=leg_id)

        if rider_id:
            rider = Rider.objects.get(id=rider_id)
        else:
            # Dynamically find the nearest rider at this moment
            start_lat = float(sub_order.pickup_latitude)
            start_lng = float(sub_order.pickup_longitude)
            prev_node = leg.start_relay_node

            logger.info(
                f"assign_rider_to_sub_order_task: Searching for nearest rider for sub-order {sub_order_id} at ({start_lat}, {start_lng})"
            )

            try:
                rider = None
                if prev_node:
                    rider = _nearest_rider_to(start_lat, start_lng, hub=prev_node)
                if not rider:
                    rider = _nearest_rider_to(start_lat, start_lng)
            except Exception as e:
                logger.error(
                    f"assign_rider_to_sub_order_task: Error searching for rider: {e}"
                )
                rider = None

            if not rider:
                logger.warning(
                    f"assign_rider_to_sub_order_task: No available rider found for sub-order {sub_order_id}"
                )
                return False

    except Exception as exc:
        logger.error(
            f"assign_rider_to_sub_order_task: missing relation or error: {exc}"
        )
        return False

    if sub_order.rider or sub_order.status not in ["Pending", "assigning"]:
        logger.info(
            f"assign_rider_to_sub_order_task: Sub-order {sub_order_id} already has a rider or is not Pending."
        )
        return False

    sub_order.rider = rider
    sub_order.status = "Assigned"
    sub_order.assigned_at = timezone.now()
    sub_order.dispatcher_assigned = True
    sub_order.save(
        update_fields=["rider", "status", "assigned_at", "dispatcher_assigned"]
    )

    leg.rider = rider
    leg.status = OrderLeg.Status.ASSIGNED
    leg.assigned_at = timezone.now()
    leg.save(update_fields=["rider", "status", "assigned_at"])

    try:
        notify_rider(
            rider=rider,
            title="Relay Leg Assigned 🔁",
            body=(
                f"You have been assigned Leg {leg.leg_number} of relay order "
                f"#{sub_order.parent_order.order_number}. Pick up from: {sub_order.pickup_address}."
            ),
            data={
                "order_number": sub_order.order_number,
                "parent_order_number": sub_order.parent_order.order_number,
                "leg_number": str(leg.leg_number),
                "status": "Assigned",
            },
        )
        publish_order_assigned_event(sub_order, rider)
    except Exception as exc:
        logger.warning(f"Relay leg assignment notification failed: {exc}")

    # Notify the merchant that a relay leg was assigned
    try:
        merchant_profile = getattr(sub_order.merchant, "merchant_profile", None)
        if merchant_profile:
            send_merchant_notification.delay(
                merchant_id=str(merchant_profile.id),
                title="Rider Assigned 🚀",
                body=(
                    f"Leg {leg.leg_number} of your relay order "
                    f"#{sub_order.parent_order.order_number} has a rider assigned."
                ),
                data={
                    "order_number": sub_order.order_number,
                    "parent_order_number": sub_order.parent_order.order_number,
                    "leg_number": str(leg.leg_number),
                    "status": "Assigned",
                },
                category="order_assigned",
            )
    except Exception as exc:
        logger.warning(f"Merchant relay leg notification failed: {exc}")

    notify_relay_vertical_leads.delay(
        parent_order_number=sub_order.parent_order.order_number,
        sub_order_ids=[str(sub_order.id)],
    )

    return True


@shared_task
def process_accepted_relay_route_task(order_id):
    """
    Background task to process an accepted relay route: create sub-orders,
    assign riders, and send notifications.
    """
    from django.db import transaction
    from django.utils import timezone
    from orders.models import Order, OrderLeg, Delivery
    from riders.notifications import notify_rider
    from riders.views import publish_order_assigned_event
    from .utils import emit_activity

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"process_accepted_relay_route_task: Order {order_id} not found.")
        return False

    legs = list(
        order.legs.select_related(
            "start_relay_node",
            "end_relay_node",
            "suggested_rider",
            "suggested_rider__user",
        ).order_by("leg_number")
    )

    first_delivery = order.deliveries.first()
    if not first_delivery:
        logger.error(
            f"process_accepted_relay_route_task: Parent order {order_id} has no delivery record."
        )
        return False

    with transaction.atomic():
        created_sub_orders = []
        cumulative_duration_minutes = 0

        for leg in legs:
            is_first_leg = leg.leg_number == 1
            is_last_leg = leg.leg_number == len(legs)

            # ── Pickup for this leg ───────────────────────────────────────
            if is_first_leg:
                # First leg always picks up from the original order origin.
                pickup_address = order.pickup_address
                pickup_lat = order.pickup_latitude
                pickup_lng = order.pickup_longitude
                pickup_sender_name = order.sender_name
                pickup_sender_phone = order.sender_phone
            else:
                # Subsequent legs pick up from the previous leg's end relay node.
                node = leg.start_relay_node
                pickup_address = node.address
                pickup_lat = node.latitude
                pickup_lng = node.longitude
                pickup_sender_name = node.name
                pickup_sender_phone = ""

            # ── Dropoff for this leg ──────────────────────────────────────
            if is_last_leg:
                # Last leg delivers to the original order destination.
                dropoff_address = first_delivery.dropoff_address
                dropoff_lat = first_delivery.dropoff_latitude
                dropoff_lng = first_delivery.dropoff_longitude
                receiver_name = first_delivery.receiver_name
                receiver_phone = first_delivery.receiver_phone
            else:
                # Intermediate legs deliver to the leg's end relay node (hub).
                node = leg.end_relay_node
                dropoff_address = node.address
                dropoff_lat = node.latitude
                dropoff_lng = node.longitude
                receiver_name = node.name
                receiver_phone = ""

            assigned_rider = leg.suggested_rider

            if is_first_leg:
                sub_status = "Assigned" if assigned_rider else "Pending"
                actual_rider = assigned_rider
            else:
                sub_status = "Pending"
                actual_rider = None

            # ── Create the sub-order ──────────────────────────────────────
            sub_order = Order.objects.create(
                user=order.user,
                rider=actual_rider,
                parent_order=order,
                relay_leg_number=leg.leg_number,
                dispatcher_assigned=True,
                mode=order.mode,
                vehicle=order.vehicle,
                pickup_address=pickup_address,
                pickup_latitude=pickup_lat,
                pickup_longitude=pickup_lng,
                sender_name=pickup_sender_name,
                sender_phone=pickup_sender_phone,
                payment_method=order.payment_method,
                payment_status="Pending",
                total_amount=leg.rider_payout,
                distance_km=leg.distance_km,
                duration_minutes=leg.duration_minutes,
                status=sub_status,
                assigned_at=timezone.now() if actual_rider else None,
                notes=(
                    f"Relay sub-order — Leg {leg.leg_number} of {len(legs)} "
                    f"for parent order {order.order_number}"
                ),
                is_relay_order=True,
            )

            # ── Create the delivery record for this sub-order ─────────────
            Delivery.objects.create(
                order=sub_order,
                pickup_address=pickup_address,
                pickup_latitude=pickup_lat,
                pickup_longitude=pickup_lng,
                sender_name=pickup_sender_name,
                sender_phone=pickup_sender_phone,
                dropoff_address=dropoff_address,
                dropoff_latitude=dropoff_lat,
                dropoff_longitude=dropoff_lng,
                receiver_name=receiver_name,
                receiver_phone=receiver_phone,
                package_type=first_delivery.package_type,
                notes=first_delivery.notes,
                sequence=leg.leg_number,
                distance_km=leg.distance_km,
                duration_minutes=leg.duration_minutes,
            )

            # ── Assign suggested rider onto the leg itself ────────────────
            leg.rider = actual_rider
            if actual_rider:
                leg.status = OrderLeg.Status.ASSIGNED
                leg.assigned_at = timezone.now()
            else:
                leg.status = "Pending"
            leg.save(update_fields=["rider", "status", "assigned_at"])

            created_sub_orders.append((leg, sub_order))

            # ── Notify the assigned rider or schedule it ─────────────────
            if assigned_rider:
                if is_first_leg:
                    try:
                        notify_rider(
                            rider=assigned_rider,
                            title="Relay Leg Assigned 🔁",
                            body=(
                                f"You have been assigned Leg {leg.leg_number} of relay order "
                                f"#{order.order_number}. Pick up from: {pickup_address}."
                            ),
                            data={
                                "order_number": sub_order.order_number,
                                "parent_order_number": order.order_number,
                                "leg_number": str(leg.leg_number),
                                "status": "Assigned",
                            },
                        )
                        publish_order_assigned_event(sub_order, assigned_rider)
                    except Exception as exc:
                        logger.warning(
                            f"Relay leg assignment notification failed: {exc}"
                        )

                    # Notify the merchant that the first relay leg has a rider
                    try:
                        merchant_profile = getattr(
                            sub_order.merchant, "merchant_profile", None
                        )
                        if merchant_profile:
                            send_merchant_notification.delay(
                                merchant_id=str(merchant_profile.id),
                                title="Rider Assigned 🚀",
                                body=(
                                    f"Leg {leg.leg_number} of your relay order "
                                    f"#{order.order_number} has a rider assigned."
                                ),
                                data={
                                    "order_number": sub_order.order_number,
                                    "parent_order_number": order.order_number,
                                    "leg_number": str(leg.leg_number),
                                    "status": "Assigned",
                                },
                                category="order_assigned",
                            )
                    except Exception as exc:
                        logger.warning(
                            f"Merchant relay notification failed: {exc}"
                        )
                else:
                    eta_time = timezone.now() + timezone.timedelta(
                        minutes=cumulative_duration_minutes
                    )
                    assign_rider_to_sub_order_task.apply_async(
                        args=[str(sub_order.id), str(leg.id), None], eta=eta_time
                    )

            cumulative_duration_minutes += leg.duration_minutes

    emit_activity(
        event_type="relay_route_accepted",
        order_id=order.order_number,
        text=f"Relay route accepted for {order.order_number} — {len(legs)} sub-orders created",
        color="green",
        metadata={
            "legs": len(legs),
            "sub_orders": [sub.order_number for _, sub in created_sub_orders],
        },
    )

    assigned_sub_ids = [str(sub.id) for _, sub in created_sub_orders if sub.rider_id]
    if assigned_sub_ids:
        # call other celery task
        notify_relay_vertical_leads.delay(
            parent_order_number=order.order_number,
            sub_order_ids=assigned_sub_ids,
        )


# ---------------------------------------------------------------------------
# Merchant Push Notifications
# ---------------------------------------------------------------------------


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_merchant_notification(self, merchant_id, title, body, data=None, category="general"):
    """
    Persist and push a notification to a merchant.

    Args:
        merchant_id (str): UUID string of the Merchant (dispatcher.Merchant.id).
        title (str): Notification title.
        body (str): Notification body text.
        data (dict | None): Arbitrary payload forwarded to the FCM message.
        category (str): Matches a toggle on MerchantNotificationSettings
                        (e.g. "order_assigned", "order_completed").

    Retries up to 3 times (10 s apart) on any unexpected failure.
    """
    from authentication.notifications import notify_merchant

    try:
        notify_merchant(merchant_id, title, body, data=data, category=category)
    except Exception as exc:
        logger.error(f"send_merchant_notification failed for merchant {merchant_id}: {exc}")
        raise self.retry(exc=exc)
    return True
