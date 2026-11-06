from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Avg, Count, Max, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from dispatcher.models import (
    DeliveryRating,
    Merchant,
    RelayNode,
    Rider,
    Vertical,
    VerticalLead,
    VehicleAsset,
    Zone,
    ZoneCaptain,
    ZoneTarget,
)
from orders.models import Order


COMPLETED_STATUS = "Done"
FAILED_STATUS = "Failed"
CANCELED_STATUSES = ["CustomerCanceled", "RiderCanceled"]


def decimal_to_float(value):
    return float(value or Decimal("0"))


def parse_period(period):
    now = timezone.now()
    today = now.date()

    if period == "today":
        start = datetime.combine(today, time.min)
        return timezone.make_aware(start), now

    if period == "yesterday":
        yesterday = today - timedelta(days=1)
        start = datetime.combine(yesterday, time.min)
        end = datetime.combine(yesterday, time.max)
        return timezone.make_aware(start), timezone.make_aware(end)

    if period == "this_week":
        monday = today - timedelta(days=today.weekday())
        start = datetime.combine(monday, time.min)
        return timezone.make_aware(start), now

    if period == "past_7_days":
        start = datetime.combine(today - timedelta(days=7), time.min)
        return timezone.make_aware(start), now

    if period == "last_month":
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        start = datetime.combine(last_month_end.replace(day=1), time.min)
        end = datetime.combine(last_month_end, time.max)
        return timezone.make_aware(start), timezone.make_aware(end)

    if period == "this_year":
        start = datetime.combine(date(today.year, 1, 1), time.min)
        return timezone.make_aware(start), now

    if period and len(period) == 7 and period.count("-") == 1:
        try:
            year, month = [int(part) for part in period.split("-")]
            start_date = date(year, month, 1)
            next_month = (
                date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
            )
            end_date = next_month - timedelta(days=1)
            start = datetime.combine(start_date, time.min)
            end = datetime.combine(end_date, time.max)
            return timezone.make_aware(start), timezone.make_aware(end)
        except ValueError:
            raise ValidationError(
                {"period": f"Invalid month '{period}'. Expected YYYY-MM."}
            )

    # Omitted or explicit "this_month" → current month to now (documented default).
    if period in (None, "", "this_month"):
        start = datetime.combine(today.replace(day=1), time.min)
        return timezone.make_aware(start), now

    # Any other non-empty value is malformed — fail loudly instead of silently
    # returning current-month data the caller did not ask for (F20).
    raise ValidationError(
        {
            "period": (
                f"Unknown period '{period}'. Use one of: today, yesterday, "
                "this_week, past_7_days, this_month, last_month, this_year, or YYYY-MM."
            )
        }
    )


@dataclass(frozen=True)
class OperationsScope:
    role: str
    vertical_ids: tuple
    zone_ids: tuple
    is_global: bool = False


def _user_name(user):
    return (
        getattr(user, "contact_name", None)
        or getattr(user, "business_name", None)
        or (user.get_full_name() if hasattr(user, "get_full_name") else "")
        or getattr(user, "phone", "")
        or getattr(user, "email", "")
        or getattr(user, "service_name", "")
    )


def get_scope(user):
    if hasattr(user, "scopes"):
        return OperationsScope("service", tuple(), tuple(), True)

    if getattr(user, "is_superuser", False):
        return OperationsScope("coo", tuple(), tuple(), True)

    dispatcher_profile = getattr(user, "dispatcher_profile", None)
    if dispatcher_profile and dispatcher_profile.role == "admin":
        return OperationsScope("coo", tuple(), tuple(), True)

    vertical_lead = getattr(user, "vertical_lead_profile", None)
    if vertical_lead and vertical_lead.is_active:
        zone_ids = tuple(
            Zone.objects.filter(vertical=vertical_lead.vertical, is_active=True)
            .values_list("id", flat=True)
        )
        return OperationsScope(
            "vertical_lead", (vertical_lead.vertical_id,), zone_ids, False
        )

    zone_lead = VerticalLead.objects.filter(user=user, is_active=True).first()
    if zone_lead:
        zone_ids = tuple(
            Zone.objects.filter(vertical=zone_lead.vertical, is_active=True)
            .values_list("id", flat=True)
        )
        return OperationsScope("vertical_lead", (zone_lead.vertical_id,), zone_ids, False)

    zone_captain = getattr(user, "zone_captain_profile", None)
    if zone_captain and zone_captain.is_active:
        vertical_id = zone_captain.zone.vertical_id
        vertical_ids = (vertical_id,) if vertical_id else tuple()
        return OperationsScope(
            "zone_captain", vertical_ids, (zone_captain.zone_id,), False
        )

    captain = ZoneCaptain.objects.filter(user=user, is_active=True).first()
    if captain:
        vertical_id = captain.zone.vertical_id
        vertical_ids = (vertical_id,) if vertical_id else tuple()
        return OperationsScope("zone_captain", vertical_ids, (captain.zone_id,), False)

    if dispatcher_profile:
        return OperationsScope(dispatcher_profile.role, tuple(), tuple(), False)

    return OperationsScope("unknown", tuple(), tuple(), False)


def scope_payload(user, scope):
    return {
        "id": str(getattr(user, "id", "")) if getattr(user, "id", None) else None,
        "name": _user_name(user) if getattr(user, "is_authenticated", False) else "",
        "role": scope.role,
        "is_global": scope.is_global,
        "vertical_ids": [str(item) for item in scope.vertical_ids],
        "zone_ids": [str(item) for item in scope.zone_ids],
        "permissions": {
            "can_view_all": scope.is_global,
            "can_view_km_integrity": scope.is_global or scope.role == "vertical_lead",
        },
    }


def scoped_verticals(scope):
    qs = Vertical.objects.filter(is_active=True)
    if not scope.is_global:
        qs = qs.filter(id__in=scope.vertical_ids)
    return qs.order_by("code")


def scoped_zones(scope):
    qs = Zone.objects.filter(is_active=True).select_related("vertical")
    if not scope.is_global:
        qs = qs.filter(id__in=scope.zone_ids)
    return qs.order_by("name")


def scoped_riders(scope):
    qs = Rider.objects.all().select_related("user", "hub", "hub__zone", "vehicle_asset")
    if not scope.is_global:
        qs = qs.filter(hub__zone_id__in=scope.zone_ids)
    return qs


def scoped_merchants(scope):
    qs = Merchant.objects.select_related("user", "zone", "zone__vertical")
    if not scope.is_global:
        qs = qs.filter(zone_id__in=scope.zone_ids)
    return qs


# Merchant activity is classified from the merchant's REAL latest order rather
# than the stored Merchant.activity_status / last_order_date fields, which are
# only maintained by seed commands in this system (audit F1/RC1). "active" =
# ordered in the last 7 days, "watch" = 8–30 days, "inactive" = 30+ days / never.
ACTIVE_WINDOW_DAYS = 7
WATCH_WINDOW_DAYS = 30


def annotate_merchant_activity(qs):
    """Annotate a Merchant queryset with the real max order timestamp."""
    return qs.annotate(_last_order_at=Max("user__orders__created_at"))


def activity_from_last_order(last_order_at, now=None):
    if last_order_at is None:
        return "inactive"
    now = now or timezone.now()
    if last_order_at >= now - timedelta(days=ACTIVE_WINDOW_DAYS):
        return "active"
    if last_order_at >= now - timedelta(days=WATCH_WINDOW_DAYS):
        return "watch"
    return "inactive"


def merchant_activity_counts(qs):
    """Bucket counts (total/active/watch/inactive) from live order recency."""
    now = timezone.now()
    counts = {"total": 0, "active": 0, "watch": 0, "inactive": 0}
    # Select id alongside the aggregate so GROUP BY is per-merchant (one row each).
    for _id, last_order_at in annotate_merchant_activity(qs).values_list("id", "_last_order_at"):
        counts["total"] += 1
        counts[activity_from_last_order(last_order_at, now)] += 1
    return counts


def scoped_hubs(scope):
    qs = RelayNode.objects.filter(is_active=True).select_related("zone", "zone__vertical")
    if not scope.is_global:
        qs = qs.filter(zone_id__in=scope.zone_ids)
    return qs.order_by("name")


def scoped_vehicles(scope):
    qs = VehicleAsset.objects.all()
    if scope.is_global:
        return qs.order_by("plate_number")

    vehicle_ids = scoped_riders(scope).exclude(vehicle_asset__isnull=True).values("vehicle_asset_id")
    return qs.filter(id__in=vehicle_ids).order_by("plate_number")


def scoped_orders(scope, start_dt=None, end_dt=None):
    qs = Order.objects.select_related(
        "rider", "rider__user", "rider__hub", "rider__hub__zone", "user"
    )
    if start_dt and end_dt:
        qs = qs.filter(created_at__gte=start_dt, created_at__lte=end_dt)
    if not scope.is_global:
        qs = qs.filter(rider__hub__zone_id__in=scope.zone_ids)
    return qs


def ensure_vertical_allowed(scope, vertical):
    if not scope.is_global and vertical.id not in scope.vertical_ids:
        raise PermissionDenied("You do not have access to this vertical.")


def ensure_zone_allowed(scope, zone):
    if not scope.is_global and zone.id not in scope.zone_ids:
        raise PermissionDenied("You do not have access to this zone.")


def ensure_rider_allowed(scope, rider):
    zone_id = rider.hub.zone_id if rider.hub and rider.hub.zone_id else None
    if not scope.is_global and zone_id not in scope.zone_ids:
        raise PermissionDenied("You do not have access to this rider.")


def ensure_vehicle_allowed(scope, vehicle):
    if scope.is_global:
        return
    if not Rider.objects.filter(vehicle_asset=vehicle, hub__zone_id__in=scope.zone_ids).exists():
        raise PermissionDenied("You do not have access to this vehicle.")


def target_for_zone(zone, start_dt):
    target = ZoneTarget.objects.filter(
        zone=zone, month__year=start_dt.year, month__month=start_dt.month
    ).first()
    if target:
        return target
    return None


def zone_target_values(zone, start_dt):
    target = target_for_zone(zone, start_dt)
    return {
        "orders": target.target_orders if target else 0,
        "revenue": decimal_to_float(target.target_revenue if target else Decimal("0")),
    }


def order_metrics(qs):
    agg = qs.aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=COMPLETED_STATUS)),
        failed=Count("id", filter=Q(status=FAILED_STATUS)),
        canceled=Count("id", filter=Q(status__in=CANCELED_STATUSES)),
        revenue=Coalesce(Sum("total_amount", filter=Q(status=COMPLETED_STATUS)), Decimal("0")),
        distance_km=Coalesce(Sum("distance_km", filter=Q(status=COMPLETED_STATUS)), Decimal("0")),
        avg_delivery_minutes=Avg("duration_minutes", filter=Q(status=COMPLETED_STATUS)),
    )
    completed = agg["completed"] or 0
    total = agg["total"] or 0
    return {
        "orders_total": total,
        "orders_completed": completed,
        "orders_failed": agg["failed"] or 0,
        "orders_canceled": agg["canceled"] or 0,
        "completion_rate": round(completed / total * 100, 1) if total else 0,
        "revenue": decimal_to_float(agg["revenue"]),
        "distance_km": decimal_to_float(agg["distance_km"]),
        "avg_delivery_minutes": round(agg["avg_delivery_minutes"] or 0, 1),
    }


def dashboard_summary(scope, period):
    start_dt, end_dt = parse_period(period)
    orders = scoped_orders(scope, start_dt, end_dt)
    metrics = order_metrics(orders)
    riders = scoped_riders(scope)
    merchants = scoped_merchants(scope)
    open_flags = build_flags(scope, limit=100)
    target_revenue = sum(
        Decimal(str(zone_target_values(zone, start_dt)["revenue"]))
        for zone in scoped_zones(scope)
    )
    return {
        "period": period,
        "range": {"start": start_dt.isoformat(), "end": end_dt.isoformat()},
        "orders": metrics,
        "riders": {
            "total": riders.count(),
            "online": riders.filter(status=Rider.Status.ONLINE).count(),
            "on_delivery": riders.filter(status=Rider.Status.ON_DELIVERY).count(),
            "offline": riders.filter(status=Rider.Status.OFFLINE).count(),
        },
        "merchants": merchant_activity_counts(merchants),
        "targets": {
            "revenue": decimal_to_float(target_revenue),
            "revenue_attainment_pct": (
                round(metrics["revenue"] / float(target_revenue) * 100, 1)
                if target_revenue
                else 0
            ),
        },
        "flags": {
            "open": len(open_flags),
            "critical": len([item for item in open_flags if item["severity"] == "critical"]),
            "warning": len([item for item in open_flags if item["severity"] == "warning"]),
        },
    }


def vertical_summary(vertical, scope, start_dt, end_dt):
    zone_ids = list(vertical.zones.filter(is_active=True).values_list("id", flat=True))
    if not scope.is_global:
        zone_ids = [item for item in zone_ids if item in scope.zone_ids]
    riders = Rider.objects.filter(hub__zone_id__in=zone_ids)
    orders = scoped_orders(scope, start_dt, end_dt).filter(rider_id__in=riders.values("id"))
    metrics = order_metrics(orders)
    target_revenue = sum(
        Decimal(str(zone_target_values(zone, start_dt)["revenue"]))
        for zone in Zone.objects.filter(id__in=zone_ids)
    )
    lead = VerticalLead.objects.select_related("user").filter(
        vertical=vertical, is_active=True
    ).first()
    return {
        "id": str(vertical.id),
        "name": vertical.name,
        "code": vertical.code,
        "lead_name": lead.user.contact_name if lead else vertical.lead_name,
        "zone_count": len(zone_ids),
        "rider_count": riders.count(),
        "merchant_count": Merchant.objects.filter(zone_id__in=zone_ids).count(),
        "orders": metrics,
        "target_revenue": decimal_to_float(target_revenue),
        "target_attainment_pct": (
            round(metrics["revenue"] / float(target_revenue) * 100, 1)
            if target_revenue
            else 0
        ),
    }


def zone_summary(zone, scope, start_dt, end_dt, include_nested=False):
    ensure_zone_allowed(scope, zone)
    riders = Rider.objects.filter(hub__zone=zone).select_related("user", "vehicle_asset", "hub")
    orders = scoped_orders(scope, start_dt, end_dt).filter(rider_id__in=riders.values("id"))
    metrics = order_metrics(orders)
    targets = zone_target_values(zone, start_dt)
    captain = ZoneCaptain.objects.select_related("user").filter(
        zone=zone, is_active=True
    ).first()
    merchants = Merchant.objects.filter(zone=zone)
    payload = {
        "id": str(zone.id),
        "name": zone.name,
        "description": zone.description,
        "vertical": {
            "id": str(zone.vertical_id) if zone.vertical_id else None,
            "name": zone.vertical.name if zone.vertical else None,
            "code": zone.vertical.code if zone.vertical else None,
        },
        "captain": {
            "id": str(captain.user_id),
            "name": _user_name(captain.user),
        } if captain else None,
        "orders": metrics,
        "targets": targets,
        "target_attainment_pct": (
            round(metrics["revenue"] / targets["revenue"] * 100, 1)
            if targets["revenue"]
            else 0
        ),
        "riders": {
            "total": riders.count(),
            "online": riders.filter(status=Rider.Status.ONLINE).count(),
            "on_delivery": riders.filter(status=Rider.Status.ON_DELIVERY).count(),
        },
        "merchants": merchant_activity_counts(merchants),
    }
    if include_nested:
        payload["rider_list"] = [rider_summary(r, start_dt, end_dt) for r in riders]
    return payload


def rider_summary(rider, start_dt, end_dt):
    orders = Order.objects.filter(rider=rider, created_at__gte=start_dt, created_at__lte=end_dt)
    metrics = order_metrics(orders)
    rating = DeliveryRating.objects.filter(
        rider=rider, created_at__gte=start_dt, created_at__lte=end_dt
    ).aggregate(avg=Avg("score"))["avg"]
    vehicle_asset = rider.vehicle_asset
    return {
        "id": str(rider.id),
        "rider_id": rider.rider_id,
        "full_name": _user_name(rider.user),
        "phone": rider.user.phone,
        "email": rider.user.email,
        "status": rider.status,
        "is_authorized": rider.is_authorized,
        "is_jumia_rider": rider.is_jumia_rider,
        "rating": float(rating if rating is not None else rider.rating or 0),
        "hub": {
            "id": str(rider.hub_id) if rider.hub_id else None,
            "name": rider.hub.name if rider.hub else None,
        },
        "zone": {
            "id": str(rider.hub.zone_id) if rider.hub and rider.hub.zone_id else None,
            "name": rider.hub.zone.name if rider.hub and rider.hub.zone else None,
        },
        "vehicle_asset": {
            "id": str(vehicle_asset.id) if vehicle_asset else None,
            "asset_id": vehicle_asset.asset_id if vehicle_asset else None,
            "plate_number": vehicle_asset.plate_number if vehicle_asset else None,
            "distance_today": decimal_to_float(vehicle_asset.distance_today) if vehicle_asset else 0,
            "deliveries_km_today": decimal_to_float(vehicle_asset.deliveries_km_today) if vehicle_asset else 0,
        },
        "orders": metrics,
        "last_location": {
            "lat": float(rider.current_latitude) if rider.current_latitude is not None else None,
            "lng": float(rider.current_longitude) if rider.current_longitude is not None else None,
            "updated_at": rider.last_location_update.isoformat() if rider.last_location_update else None,
            "speed": float(rider.current_speed or 0),
            "is_moving": rider.is_moving,
        },
    }


def rider_performance(rider, start_dt, end_dt):
    """Rider detail + a performance block computed only from data we actually
    have (F15). Metrics with no real source (acceptance_rate, ghost_ratio,
    peak_util) are intentionally NOT returned rather than fabricated."""
    payload = rider_summary(rider, start_dt, end_dt)
    metrics = payload["orders"]
    distance = metrics["distance_km"]
    active_days = (
        Order.objects.filter(rider=rider, created_at__gte=start_dt, created_at__lte=end_dt)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .distinct()
        .count()
    )
    payload["performance"] = {
        # Naira of completed-order revenue per delivered km.
        "rev_per_km": round(metrics["revenue"] / distance, 1) if distance else 0,
        "avg_delivery_minutes": metrics["avg_delivery_minutes"],
        # Average delivery rating in the period (0 if no ratings captured yet).
        "csat_avg": payload["rating"],
        # Distinct calendar days the rider had at least one order in the period.
        "active_days": active_days,
    }
    return payload


def merchant_summary(merchant, start_dt, end_dt):
    orders = Order.objects.filter(user=merchant.user, created_at__gte=start_dt, created_at__lte=end_dt)
    metrics = order_metrics(orders)
    # Derive activity from the real latest order (annotated when called from a
    # list; otherwise queried) instead of the stale stored field (F1).
    if hasattr(merchant, "_last_order_at"):
        last_order_at = merchant._last_order_at
    else:
        last_order_at = Order.objects.filter(user=merchant.user).aggregate(
            last=Max("created_at")
        )["last"]
    return {
        "id": str(merchant.id),
        "merchant_id": merchant.merchant_id,
        "business_name": merchant.user.business_name or merchant.user.contact_name or "",
        "phone": merchant.user.phone,
        "email": merchant.user.email,
        "activity_status": activity_from_last_order(last_order_at),
        "merchant_type": merchant.merchant_type,
        "is_partner": merchant.is_partner,
        "has_active_subscription": merchant.has_active_subscription,
        "has_price_list": merchant.has_price_list,
        "last_order_date": last_order_at.isoformat() if last_order_at else None,
        "zone": {
            "id": str(merchant.zone_id) if merchant.zone_id else None,
            "name": merchant.zone.name if merchant.zone else None,
        },
        "orders": metrics,
    }


def order_summary(order):
    rider = order.rider
    zone = rider.hub.zone if rider and rider.hub and rider.hub.zone else None
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "mode": order.mode,
        "source": order.source,
        "partner": order.partner,
        "is_partner_order": order.is_partner_order,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "total_amount": decimal_to_float(order.total_amount),
        "distance_km": decimal_to_float(order.distance_km),
        "duration_minutes": order.duration_minutes or 0,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "completed_at": order.completed_at.isoformat() if order.completed_at else None,
        "merchant": {
            "id": str(order.user_id),
            "name": order.user.business_name or order.user.contact_name or "",
            "phone": order.user.phone,
        },
        "rider": {
            "id": str(rider.id) if rider else None,
            "rider_id": rider.rider_id if rider else None,
            "name": _user_name(rider.user) if rider else None,
        },
        "zone": {
            "id": str(zone.id) if zone else None,
            "name": zone.name if zone else None,
        },
    }


def orders_list(scope, period, filters):
    start_dt, end_dt = parse_period(period)
    qs = scoped_orders(scope, start_dt, end_dt).order_by("-created_at")

    status = filters.get("status")
    if status:
        qs = qs.filter(status=status)

    zone_id = filters.get("zone_id")
    if zone_id:
        qs = qs.filter(rider__hub__zone_id=zone_id)

    rider_id = filters.get("rider_id")
    if rider_id:
        qs = qs.filter(rider_id=rider_id)

    merchant_id = filters.get("merchant_id")
    if merchant_id:
        qs = qs.filter(user_id=merchant_id)

    limit = min(int(filters.get("limit") or 100), 500)
    offset = max(int(filters.get("offset") or 0), 0)
    total = qs.count()
    page = qs[offset:offset + limit]
    return {
        "period": period,
        "count": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
        "results": [order_summary(order) for order in page],
    }


def orders_analytics(scope, period):
    start_dt, end_dt = parse_period(period)
    qs = scoped_orders(scope, start_dt, end_dt)
    by_status = [
        {"status": row["status"], "count": row["count"]}
        for row in qs.values("status").annotate(count=Count("id")).order_by("status")
    ]
    by_source = [
        {"source": row["source"], "count": row["count"]}
        for row in qs.values("source").annotate(count=Count("id")).order_by("source")
    ]
    # Metrics for the days that actually have orders (one query per such day).
    day_metrics = {
        row["day"]: order_metrics(qs.filter(created_at__date=row["day"]))
        for row in qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        if row["day"]
    }
    # Emit a row for EVERY calendar day in the range so charts align with
    # rider daily-activity (F16); days without orders get zeroed metrics.
    zero_metrics = {
        "orders_total": 0,
        "orders_completed": 0,
        "orders_failed": 0,
        "orders_canceled": 0,
        "completion_rate": 0,
        "revenue": 0.0,
        "distance_km": 0.0,
        "avg_delivery_minutes": 0,
    }
    by_day = []
    current = start_dt.date()
    end_date = end_dt.date()
    while current <= end_date:
        by_day.append({"date": current.isoformat(), **day_metrics.get(current, zero_metrics)})
        current += timedelta(days=1)
    return {
        "period": period,
        "range": {"start": start_dt.isoformat(), "end": end_dt.isoformat()},
        "summary": order_metrics(qs),
        "by_status": by_status,
        "by_source": by_source,
        "by_day": by_day,
    }


def merchants_list(scope, period, filters):
    start_dt, end_dt = parse_period(period)
    # Annotate live last-order time so merchant_summary reads it (no N+1) and the
    # activity filter operates on real recency, not the stale stored field (F1).
    qs = annotate_merchant_activity(scoped_merchants(scope)).order_by(
        "user__business_name", "merchant_id"
    )

    zone_id = filters.get("zone_id")
    if zone_id:
        qs = qs.filter(zone_id=zone_id)

    activity_status = filters.get("activity_status") or filters.get("status")
    if activity_status:
        now = timezone.now()
        active_cutoff = now - timedelta(days=ACTIVE_WINDOW_DAYS)
        watch_cutoff = now - timedelta(days=WATCH_WINDOW_DAYS)
        if activity_status == "active":
            qs = qs.filter(_last_order_at__gte=active_cutoff)
        elif activity_status == "watch":
            qs = qs.filter(_last_order_at__gte=watch_cutoff, _last_order_at__lt=active_cutoff)
        elif activity_status == "inactive":
            qs = qs.filter(Q(_last_order_at__lt=watch_cutoff) | Q(_last_order_at__isnull=True))

    is_partner = filters.get("is_partner")
    if is_partner in ("true", "false"):
        qs = qs.filter(is_partner=(is_partner == "true"))

    limit = min(int(filters.get("limit") or 100), 500)
    return {
        "period": period,
        "count": qs.count(),
        "results": [merchant_summary(merchant, start_dt, end_dt) for merchant in qs[:limit]],
    }


def hub_summary(hub, start_dt, end_dt):
    riders = Rider.objects.filter(hub=hub).select_related("user", "vehicle_asset")
    orders = Order.objects.filter(rider__hub=hub, created_at__gte=start_dt, created_at__lte=end_dt)
    return {
        "id": str(hub.id),
        "name": hub.name,
        "address": hub.address,
        "latitude": hub.latitude,
        "longitude": hub.longitude,
        "catchment_radius_km": hub.catchment_radius_km,
        "hub_captain_name": hub.hub_captain_name,
        "hub_captain_phone": hub.hub_captain_phone,
        "zone": {
            "id": str(hub.zone_id) if hub.zone_id else None,
            "name": hub.zone.name if hub.zone else None,
            "vertical": hub.zone.vertical.name if hub.zone and hub.zone.vertical else None,
        },
        "riders": {
            "total": riders.count(),
            "online": riders.filter(status=Rider.Status.ONLINE).count(),
            "on_delivery": riders.filter(status=Rider.Status.ON_DELIVERY).count(),
        },
        "orders": order_metrics(orders),
    }


def hubs_list(scope, period, filters):
    start_dt, end_dt = parse_period(period)
    qs = scoped_hubs(scope)
    zone_id = filters.get("zone_id")
    if zone_id:
        qs = qs.filter(zone_id=zone_id)
    return {
        "period": period,
        "count": qs.count(),
        "results": [hub_summary(hub, start_dt, end_dt) for hub in qs],
    }


def vehicle_summary(vehicle):
    rider = Rider.objects.select_related("user", "hub", "hub__zone").filter(vehicle_asset=vehicle).first()
    zone = rider.hub.zone if rider and rider.hub and rider.hub.zone else None
    gps_km = vehicle.distance_today or Decimal("0")
    order_km = vehicle.deliveries_km_today or Decimal("0")
    denominator = max(gps_km, order_km)
    variance_pct = (
        round(float(abs(gps_km - order_km) / denominator * Decimal("100")), 1)
        if denominator
        else 0
    )
    return {
        "id": str(vehicle.id),
        "asset_id": vehicle.asset_id,
        "plate_number": vehicle.plate_number,
        "vehicle_type": vehicle.vehicle_type,
        "make": vehicle.make,
        "model": vehicle.model,
        "year": vehicle.year,
        "color": vehicle.color,
        "engine_status": vehicle.engine_status,
        "is_active": vehicle.is_active,
        "provider_id": vehicle.provider_id,
        "total_distance": decimal_to_float(vehicle.total_distance),
        "unit_of_distance": vehicle.unit_of_distance,
        "distance_today": decimal_to_float(vehicle.distance_today),
        "deliveries_km_today": decimal_to_float(vehicle.deliveries_km_today),
        "km_variance_pct": variance_pct,
        "km_integrity_status": km_integrity_status(vehicle.distance_today, vehicle.deliveries_km_today),
        "speed": decimal_to_float(vehicle.speed),
        "last_telemetry_at": vehicle.last_telemetry_at.isoformat() if vehicle.last_telemetry_at else None,
        "location": {
            "lat": float(vehicle.latitude) if vehicle.latitude is not None else None,
            "lng": float(vehicle.longitude) if vehicle.longitude is not None else None,
            "course": float(vehicle.course) if vehicle.course is not None else None,
        },
        "assigned_rider": {
            "id": str(rider.id) if rider else None,
            "rider_id": rider.rider_id if rider else None,
            "name": _user_name(rider.user) if rider else None,
        },
        "zone": {
            "id": str(zone.id) if zone else None,
            "name": zone.name if zone else None,
        },
    }


def vehicles_list(scope, filters):
    qs = scoped_vehicles(scope)
    status = filters.get("status")
    if status == "active":
        qs = qs.filter(is_active=True)
    elif status == "inactive":
        qs = qs.filter(is_active=False)
    return {"count": qs.count(), "results": [vehicle_summary(vehicle) for vehicle in qs[:500]]}


def rider_vehicle(scope, rider):
    ensure_rider_allowed(scope, rider)
    if not rider.vehicle_asset:
        return {
            "rider_id": str(rider.id),
            "vehicle": None,
            "message": "No vehicle asset is assigned to this rider.",
        }
    return {"rider_id": str(rider.id), "vehicle": vehicle_summary(rider.vehicle_asset)}


def km_integrity_status(gps_km, order_km):
    gps_km = gps_km or Decimal("0")
    order_km = order_km or Decimal("0")
    denominator = max(gps_km, order_km)
    if not denominator:
        return "unavailable"
    variance = abs(gps_km - order_km) / denominator
    if variance > Decimal("0.10"):
        return "failed"
    return "passed"


def km_visibility(scope):
    vehicles = [vehicle_summary(vehicle) for vehicle in scoped_vehicles(scope)[:500]]
    return {
        "count": len(vehicles),
        "available": len([v for v in vehicles if v["km_integrity_status"] != "unavailable"]),
        "failed": len([v for v in vehicles if v["km_integrity_status"] == "failed"]),
        "passed": len([v for v in vehicles if v["km_integrity_status"] == "passed"]),
        "results": vehicles,
    }


def km_integrity(scope, filters):
    status = filters.get("status")
    rows = km_visibility(scope)["results"]
    if status:
        rows = [row for row in rows if row["km_integrity_status"] == status]
    return {
        "count": len(rows),
        "results": rows,
    }


def rider_daily_activity(rider, start_dt, end_dt):
    rows = []
    current = start_dt.date()
    end_date = end_dt.date()
    while current <= end_date:
        day_start = timezone.make_aware(datetime.combine(current, time.min))
        day_end = timezone.make_aware(datetime.combine(current, time.max))
        metrics = order_metrics(
            Order.objects.filter(rider=rider, created_at__gte=day_start, created_at__lte=day_end)
        )
        rows.append({"date": current.isoformat(), **metrics})
        current += timedelta(days=1)
    return rows


def build_flags(scope, limit=50):
    flags = []
    for rider in scoped_riders(scope).filter(status=Rider.Status.OFFLINE, current_speed__gt=5)[:limit]:
        flags.append(
            {
                "type": "ghost_ride",
                "severity": "warning",
                "message": "Rider is offline but GPS speed indicates movement.",
                "rider_id": str(rider.id),
                "rider_name": _user_name(rider.user),
                "zone_id": str(rider.hub.zone_id) if rider.hub and rider.hub.zone_id else None,
            }
        )

    remaining = max(0, limit - len(flags))
    riders_with_assets = scoped_riders(scope).exclude(vehicle_asset__isnull=True)[: max(remaining, 0)]
    for rider in riders_with_assets:
        if len(flags) >= limit:
            break
        asset = rider.vehicle_asset
        gps_km = asset.distance_today or Decimal("0")
        order_km = asset.deliveries_km_today or Decimal("0")
        denominator = max(gps_km, order_km)
        if denominator and abs(gps_km - order_km) / denominator > Decimal("0.10"):
            flags.append(
                {
                    "type": "km_integrity",
                    "severity": "critical",
                    "message": "GPS KM and completed-order KM differ by more than 10%.",
                    "rider_id": str(rider.id),
                    "rider_name": _user_name(rider.user),
                    "zone_id": str(rider.hub.zone_id) if rider.hub and rider.hub.zone_id else None,
                    "gps_km": decimal_to_float(gps_km),
                    "order_km": decimal_to_float(order_km),
                }
            )
    return flags


def leaderboard(scope, period):
    start_dt, end_dt = parse_period(period)
    zones = [
        zone_summary(zone, scope, start_dt, end_dt)
        for zone in scoped_zones(scope).select_related("vertical")
    ]
    zone_rankings = sorted(
        zones, key=lambda item: item["orders"]["revenue"], reverse=True
    )
    for index, item in enumerate(zone_rankings, start=1):
        item["rank"] = index

    riders = [
        rider_summary(rider, start_dt, end_dt)
        for rider in scoped_riders(scope)[:500]
    ]
    # Only rank riders who actually had orders in the period. This drops the
    # test/admin/hub-less accounts (Super Admin, Test Ignore, …) that otherwise
    # padded the bottom of the board with zero-order rows (F9).
    active_riders = [item for item in riders if item["orders"]["orders_total"] > 0]
    rider_rankings = sorted(
        active_riders, key=lambda item: item["orders"]["orders_completed"], reverse=True
    )[:50]
    for index, item in enumerate(rider_rankings, start=1):
        item["rank"] = index

    verticals = [
        vertical_summary(v, scope, start_dt, end_dt)
        for v in scoped_verticals(scope).prefetch_related("zones")
    ]
    vertical_rankings = sorted(
        verticals, key=lambda item: item["orders"]["revenue"], reverse=True
    )
    for index, item in enumerate(vertical_rankings, start=1):
        item["rank"] = index

    return {
        "period": period,
        "zones": zone_rankings,
        "riders": rider_rankings,
        "verticals": vertical_rankings,
    }
