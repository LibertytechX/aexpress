"""
OCC (Operations Command Center) analytics endpoints.

All views use ServiceAPIKeyAuthentication + HasOCCReadScope.
The OCC backend calls these server-to-server using a service API key.
"""

import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db import models
from django.db.models import (
    Avg,
    Count,
    F,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, ExtractHour
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import ServiceAPIKeyAuthentication
from .models import (
    DeliveryRating,
    Merchant,
    MerchantDailySnapshot,
    Rider,
    RiderDailySnapshot,
    RiderDutyLog,
    Vertical,
    VerticalLead,
    Zone,
    ZoneCaptain,
    ZoneTarget,
)
from .permissions import HasOCCReadScope, HasOCCWriteScope

# Vertical color mapping
VERTICAL_COLORS = {
    "A": "#3B82F6",
    "B": "#10B981",
    "C": "#F59E0B",
    "D": "#EF4444",
}


# ---------------------------------------------------------------------------
# Period helpers
# ---------------------------------------------------------------------------


def _parse_period(period_str):
    """
    Return (start_dt, end_dt, is_fully_elapsed) for the requested period.
    All datetimes are timezone-aware (Africa/Lagos).
    """
    now = timezone.now()
    today = now.date()

    if period_str == "today":
        start = datetime.combine(today, time.min)
        end = now
        return timezone.make_aware(start), end, False

    if period_str == "yesterday":
        yesterday = today - timedelta(days=1)
        start = datetime.combine(yesterday, time.min)
        end = datetime.combine(yesterday, time.max)
        return timezone.make_aware(start), timezone.make_aware(end), True

    if period_str == "this_week":
        monday = today - timedelta(days=today.weekday())
        start = datetime.combine(monday, time.min)
        end = now
        return timezone.make_aware(start), end, False

    if period_str == "past_7_days":
        start = datetime.combine(today - timedelta(days=7), time.min)
        end = now
        return timezone.make_aware(start), end, True

    if period_str == "this_month":
        start = datetime.combine(today.replace(day=1), time.min)
        end = now
        return timezone.make_aware(start), end, False

    if period_str == "last_month":
        first_this = today.replace(day=1)
        last_month_end = first_this - timedelta(days=1)
        start = datetime.combine(last_month_end.replace(day=1), time.min)
        end = datetime.combine(last_month_end, time.max)
        return timezone.make_aware(start), timezone.make_aware(end), True

    if period_str == "this_year":
        start = datetime.combine(date(today.year, 1, 1), time.min)
        end = now
        return timezone.make_aware(start), end, False

    # YYYY-MM format
    try:
        parts = period_str.split("-")
        year, month = int(parts[0]), int(parts[1])
        last_day = calendar.monthrange(year, month)[1]
        start = datetime.combine(date(year, month, 1), time.min)
        end = datetime.combine(date(year, month, last_day), time.max)
        return timezone.make_aware(start), timezone.make_aware(end), True
    except (ValueError, IndexError):
        pass

    # Default to this_month
    start = datetime.combine(today.replace(day=1), time.min)
    end = now
    return timezone.make_aware(start), end, False


def _scale_target(full_monthly, period_str):
    """Scale a monthly target to the requested period."""
    now = timezone.now()
    today = now.date()

    if period_str == "today":
        return full_monthly / Decimal("26")
    if period_str == "yesterday":
        return full_monthly / Decimal("26")
    if period_str == "this_week":
        days_in = today.weekday() + 1
        return full_monthly / Decimal("26") * Decimal(str(days_in))
    if period_str == "past_7_days":
        return full_monthly / Decimal("26") * Decimal("7")
    if period_str in ("this_month", "last_month"):
        return full_monthly
    if period_str == "this_year":
        return full_monthly * Decimal(str(today.month))
    return full_monthly


def _order_qs_for_period(start_dt, end_dt):
    """Return base Order queryset filtered to the period."""
    from orders.models import Order

    return Order.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt)


def _build_rider_data(rider, start_dt, end_dt, period, zone_target=None):
    """Build rider performance dict for embedding in zone/vertical responses."""
    from riders.models import OrderOffer

    orders_qs = _order_qs_for_period(start_dt, end_dt).filter(rider=rider)
    completed = orders_qs.filter(status="Done").count()
    failed = orders_qs.filter(status="Failed").count()

    revenue = orders_qs.filter(status="Done").aggregate(
        rev=Coalesce(Sum("total_amount"), Decimal("0"))
    )["rev"]
    distance = orders_qs.filter(status="Done").aggregate(
        dist=Coalesce(Sum("distance_km"), Decimal("0"))
    )["dist"]
    avg_delivery_time = orders_qs.filter(status="Done").aggregate(
        avg_time=Avg("duration_minutes")
    )["avg_time"]

    # Acceptance rate
    offers = OrderOffer.objects.filter(
        rider=rider, created_at__gte=start_dt, created_at__lte=end_dt
    )
    total_offers = offers.count()
    declined = offers.filter(status="declined").count()
    acceptance_rate = (
        round((1 - declined / total_offers) * 100, 1) if total_offers else 100.0
    )

    # CSAT
    csat = DeliveryRating.objects.filter(
        rider=rider, created_at__gte=start_dt, created_at__lte=end_dt
    ).aggregate(avg=Avg("score"))["avg"]

    # Duty logs
    duty_logs = RiderDutyLog.objects.filter(
        rider=rider, went_online__gte=start_dt, went_online__lte=end_dt
    )
    online_minutes = sum(d.duration_minutes or 0 for d in duty_logs)
    period_days = max((end_dt - start_dt).days, 1)
    online_days = min(round(online_minutes / 480), period_days)  # 8hr workday

    # Ghost minutes
    ghost_minutes = 0
    for d in duty_logs:
        if d.duration_minutes and d.went_online and d.went_offline:
            if rider.status == "offline":
                ghost_minutes += max(0, (d.duration_minutes or 0) // 10)

    ghost_ratio = (
        round(ghost_minutes / max(online_minutes, 1) * 100, 1)
        if online_minutes else 0
    )

    # Peak hours
    peak_minutes = 0
    peak_orders = 0
    for d in duty_logs:
        if d.duration_minutes and d.went_online:
            h = d.went_online.hour
            if (12 <= h < 15) or (17 <= h < 20):
                peak_minutes += d.duration_minutes

    peak_orders = orders_qs.filter(
        status="Done", created_at__hour__gte=12, created_at__hour__lt=15
    ).count() + orders_qs.filter(
        status="Done", created_at__hour__gte=17, created_at__hour__lt=20
    ).count()

    peak_util = (
        round(peak_minutes / max(online_minutes, 1) * 100, 1)
        if online_minutes else 0
    )

    rev_per_km = round(float(revenue) / float(distance), 0) if distance else 0
    failed_rate = round(failed / max(completed + failed, 1) * 100, 1)

    # Target calculations
    target_orders = 0
    target_revenue = 0
    pct = 0
    if zone_target:
        rider_count = Rider.objects.filter(home_zone=rider.home_zone).count()
        if rider_count:
            target_orders = round(
                float(_scale_target(zone_target.target_orders, period)) / rider_count
            )
            target_revenue = round(
                float(_scale_target(zone_target.target_revenue, period)) / rider_count
            )
            pct = round(completed / max(target_orders, 1) * 100)

    # Flags
    flags = []
    if ghost_ratio > 5:
        flags.append({"type": "warning", "msg": "High ghost-ride ratio"})
    if acceptance_rate < 70:
        flags.append({"type": "critical", "msg": f"Low acceptance rate ({acceptance_rate}%)"})
    if csat and csat < 3.5:
        flags.append({"type": "warning", "msg": f"Low CSAT ({round(csat, 1)})"})
    if failed_rate > 10:
        flags.append({"type": "warning", "msg": f"High failed rate ({failed_rate}%)"})

    return {
        "id": str(rider.id),
        "full_name": rider.user.contact_name or rider.user.get_full_name(),
        "status": rider.status,
        "orders_completed": completed,
        "orders_rejected": declined,
        "orders_failed": failed,
        "revenue": float(revenue),
        "km_covered": float(distance),
        "online_days": online_days,
        "avg_delivery_mins": round(avg_delivery_time, 1) if avg_delivery_time else 0,
        "csat_avg": round(csat, 1) if csat else None,
        "ghost_minutes": ghost_minutes,
        "ghost_ratio": ghost_ratio,
        "peak_orders": peak_orders,
        "peak_util": peak_util,
        "rev_per_km": rev_per_km,
        "acceptance_rate": acceptance_rate,
        "failed_rate": failed_rate,
        "target_orders": target_orders,
        "target_revenue": target_revenue,
        "pct": pct,
        "flags": flags,
    }


def _build_merchant_data(merchant, start_dt, end_dt):
    """Build merchant summary dict for embedding in zone/vertical responses."""
    orders_qs = _order_qs_for_period(start_dt, end_dt).filter(user=merchant.user)
    total_orders = orders_qs.count()
    completed = orders_qs.filter(status="Done").count()
    returned = orders_qs.filter(status="Failed").count()
    revenue = orders_qs.filter(status="Done").aggregate(
        rev=Coalesce(Sum("total_amount"), Decimal("0"))
    )["rev"]
    avg_order_value = (
        round(float(revenue) / completed) if completed else 0
    )
    fulfillment_rate = round(completed / total_orders * 100, 1) if total_orders else 0

    days_since = None
    if merchant.last_order_date:
        days_since = (timezone.now() - merchant.last_order_date).days

    return {
        "id": str(merchant.id),
        "business_name": merchant.user.business_name or "Unknown",
        "business_type": getattr(merchant.user, "business_type", "") or "",
        "zone_name": merchant.zone.name if merchant.zone else "",
        "status": merchant.activity_status,
        "orders_placed": total_orders,
        "orders_fulfilled": completed,
        "orders_returned": returned,
        "gross_revenue": float(revenue),
        "avg_order_value": avg_order_value,
        "fulfillment_rate": fulfillment_rate,
        "days_since_order": days_since,
    }


# ---------------------------------------------------------------------------
# Vertical endpoints
# ---------------------------------------------------------------------------


class OCCVerticalListView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request):
        period = request.query_params.get("period", "this_month")
        start_dt, end_dt, _ = _parse_period(period)

        verticals = Vertical.objects.filter(is_active=True).prefetch_related("zones")
        result = []

        for v in verticals:
            zone_ids = list(v.zones.filter(is_active=True).values_list("id", flat=True))
            rider_ids = list(
                Rider.objects.filter(home_zone_id__in=zone_ids).values_list(
                    "id", flat=True
                )
            )

            # TODO: switch to snapshot table once populated
            orders_qs = _order_qs_for_period(start_dt, end_dt).filter(
                rider_id__in=rider_ids
            )
            agg = orders_qs.aggregate(
                total=Count("id"),
                completed=Count("id", filter=Q(status="Done")),
                revenue=Coalesce(
                    Sum("total_amount", filter=Q(status="Done")), Decimal("0")
                ),
            )

            merchant_count = Merchant.objects.filter(zone_id__in=zone_ids).count()

            # Target
            targets = ZoneTarget.objects.filter(
                zone_id__in=zone_ids,
                month__year=start_dt.year,
                month__month=start_dt.month,
            )
            total_target_rev = sum(
                _scale_target(t.target_revenue, period) for t in targets
            ) or Decimal("1")
            target_pct = round(
                float(agg["revenue"]) / float(total_target_rev) * 100, 1
            )

            # Captain info
            lead_info = None
            try:
                vl = VerticalLead.objects.select_related("user").get(
                    vertical=v, is_active=True
                )
                lead_info = {
                    "id": str(vl.user.id),
                    "name": vl.user.contact_name or vl.user.get_full_name(),
                }
            except VerticalLead.DoesNotExist:
                pass

            result.append(
                {
                    "id": str(v.id),
                    "name": v.name,
                    "code": v.code,
                    "lead_name": v.lead_name,
                    "lead": lead_info,
                    "zone_count": len(zone_ids),
                    "rider_count": len(rider_ids),
                    "merchant_count": merchant_count,
                    "orders_count": agg["total"],
                    "orders_completed": agg["completed"],
                    "revenue": str(agg["revenue"]),
                    "target_attainment_pct": target_pct,
                }
            )

        return Response(result)


class OCCVerticalDetailView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request, pk):
        period = request.query_params.get("period", "this_month")
        start_dt, end_dt, _ = _parse_period(period)

        try:
            v = Vertical.objects.prefetch_related("zones").get(pk=pk)
        except Vertical.DoesNotExist:
            return Response(
                {"error": "Vertical not found"}, status=status.HTTP_404_NOT_FOUND
            )

        zones_data = []
        total_orders = 0
        total_revenue = Decimal("0")

        for z in v.zones.filter(is_active=True):
            zone_riders = list(
                Rider.objects.filter(home_zone=z).select_related("user", "vehicle_asset")
            )
            rider_ids = [r.id for r in zone_riders]

            orders_qs = _order_qs_for_period(start_dt, end_dt).filter(
                rider_id__in=rider_ids
            )
            agg = orders_qs.aggregate(
                total=Count("id"),
                completed=Count("id", filter=Q(status="Done")),
                revenue=Coalesce(
                    Sum("total_amount", filter=Q(status="Done")), Decimal("0")
                ),
            )
            total_orders += agg["total"]
            total_revenue += agg["revenue"]

            captain_name = None
            captain_pay = 0
            try:
                zc = ZoneCaptain.objects.select_related("user").get(
                    zone=z, is_active=True
                )
                captain_name = zc.user.contact_name or zc.user.get_full_name()
                # Captain pay: 50k base + 40k transport + 4% gross rev
                captain_pay = round(
                    float(Decimal("90000") + agg["revenue"] * Decimal("0.04"))
                )
            except ZoneCaptain.DoesNotExist:
                pass

            # Zone target
            zone_target = None
            target_rev = Decimal("600000")
            try:
                zone_target = ZoneTarget.objects.get(
                    zone=z,
                    month__year=start_dt.year,
                    month__month=start_dt.month,
                )
                target_rev = _scale_target(zone_target.target_revenue, period)
            except ZoneTarget.DoesNotExist:
                target_rev = _scale_target(target_rev, period)

            target_pct = (
                round(float(agg["revenue"]) / float(target_rev) * 100, 1)
                if target_rev
                else 0
            )

            # Merchant aggregates
            zone_merchants = list(
                Merchant.objects.filter(zone=z).select_related("user", "zone")
            )
            merchant_agg = {
                "total": len(zone_merchants),
                "active": sum(1 for m in zone_merchants if m.activity_status == "active"),
                "watch": sum(1 for m in zone_merchants if m.activity_status == "watch"),
                "inactive": sum(1 for m in zone_merchants if m.activity_status == "inactive"),
            }

            # Build riders array
            riders_list = []
            for r in zone_riders:
                riders_list.append(
                    _build_rider_data(r, start_dt, end_dt, period, zone_target)
                )

            # Build merchants_list array
            merchants_detail = []
            for m in zone_merchants:
                merchants_detail.append(_build_merchant_data(m, start_dt, end_dt))

            zones_data.append(
                {
                    "id": str(z.id),
                    "name": z.name,
                    "captain": captain_name,
                    "orders": agg["total"],
                    "target": round(float(target_rev)),
                    "perf_pct": target_pct,
                    "captain_pay": captain_pay,
                    "merchants": merchant_agg,
                    "riders": riders_list,
                    "merchants_list": merchants_detail,
                }
            )

        return Response(
            {
                "id": str(v.id),
                "name": v.name,
                "code": v.code,
                "lead_name": v.lead_name,
                "zones": zones_data,
                "aggregates": {
                    "orders": total_orders,
                    "revenue": str(total_revenue),
                    "active_riders": Rider.objects.filter(
                        home_zone__vertical=v, status="online"
                    ).count(),
                    "active_merchants": Merchant.objects.filter(
                        zone__vertical=v, activity_status="active"
                    ).count(),
                },
            }
        )


class OCCVerticalZonesView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request, pk):
        """Same as detail view zones section — convenience alias."""
        detail_view = OCCVerticalDetailView()
        detail_view.request = request
        response = detail_view.get(request, pk)
        if response.status_code == 200:
            return Response(response.data.get("zones", []))
        return response


# ---------------------------------------------------------------------------
# Zone endpoints
# ---------------------------------------------------------------------------


class OCCZoneDashboardView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request, pk):
        period = request.query_params.get("period", "this_month")
        start_dt, end_dt, _ = _parse_period(period)

        try:
            zone = Zone.objects.get(pk=pk)
        except Zone.DoesNotExist:
            return Response(
                {"error": "Zone not found"}, status=status.HTTP_404_NOT_FOUND
            )

        rider_ids = list(
            Rider.objects.filter(home_zone=zone).values_list("id", flat=True)
        )

        # TODO: switch to snapshot table once populated
        orders_qs = _order_qs_for_period(start_dt, end_dt).filter(
            rider_id__in=rider_ids
        )
        agg = orders_qs.aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(status="Done")),
            failed=Count("id", filter=Q(status="Failed")),
            canceled=Count(
                "id", filter=Q(status__in=["CustomerCanceled", "RiderCanceled"])
            ),
            revenue=Coalesce(
                Sum("total_amount", filter=Q(status="Done")), Decimal("0")
            ),
            avg_distance=Coalesce(
                Avg("distance_km", filter=Q(status="Done")),
                Decimal("0"),
                output_field=models.DecimalField(),
            ),
            avg_duration=Coalesce(
                Avg("duration_minutes", filter=Q(status="Done")),
                0,
                output_field=models.FloatField(),
            ),
        )

        # Target
        target_rev = Decimal("600000")
        try:
            zt = ZoneTarget.objects.get(
                zone=zone,
                month__year=start_dt.year,
                month__month=start_dt.month,
            )
            target_rev = _scale_target(zt.target_revenue, period)
        except ZoneTarget.DoesNotExist:
            target_rev = _scale_target(target_rev, period)

        target_pct = (
            round(float(agg["revenue"]) / float(target_rev) * 100, 1)
            if target_rev
            else 0
        )

        return Response(
            {
                "zone_id": str(zone.id),
                "zone_name": zone.name,
                "orders_total": agg["total"],
                "orders_completed": agg["completed"],
                "orders_failed": agg["failed"],
                "orders_canceled": agg["canceled"],
                "revenue": str(agg["revenue"]),
                "avg_delivery_time": agg["avg_duration"],
                "avg_distance_km": str(agg["avg_distance"]),
                "rider_count": len(rider_ids),
                "active_riders": Rider.objects.filter(
                    home_zone=zone, status="online"
                ).count(),
                "merchant_count": Merchant.objects.filter(zone=zone).count(),
                "active_merchants": Merchant.objects.filter(
                    zone=zone, activity_status="active"
                ).count(),
                "target_attainment_pct": target_pct,
            }
        )


class OCCZoneRidersView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request, pk):
        period = request.query_params.get("period", "this_month")
        start_dt, end_dt, _ = _parse_period(period)

        riders = Rider.objects.filter(home_zone_id=pk).select_related("user")

        result = []
        for r in riders:
            # TODO: switch to snapshot table once populated
            orders_qs = _order_qs_for_period(start_dt, end_dt).filter(rider=r)
            completed = orders_qs.filter(status="Done").count()
            failed = orders_qs.filter(status="Failed").count()
            total = orders_qs.count()

            # Revenue
            revenue = (
                orders_qs.filter(status="Done").aggregate(
                    rev=Coalesce(Sum("total_amount"), Decimal("0"))
                )["rev"]
            )

            # Distance
            distance = (
                orders_qs.filter(status="Done").aggregate(
                    dist=Coalesce(Sum("distance_km"), Decimal("0"))
                )["dist"]
            )

            # Acceptance rate from OrderOffer
            from riders.models import OrderOffer

            offers = OrderOffer.objects.filter(
                rider=r, created_at__gte=start_dt, created_at__lte=end_dt
            )
            total_offers = offers.count()
            declined = offers.filter(status="declined").count()
            acceptance_rate = (
                round((1 - declined / total_offers) * 100, 1) if total_offers else 100.0
            )

            # CSAT
            csat = DeliveryRating.objects.filter(
                rider=r, created_at__gte=start_dt, created_at__lte=end_dt
            ).aggregate(avg=Avg("score"))["avg"]

            # Ghost ride flag — check if rider is offline but vehicle asset is moving
            ghost_flag = False
            if r.status == "offline" and r.vehicle_asset:
                ghost_flag = float(r.vehicle_asset.speed or 0) > 5

            # Online days ratio from duty logs
            duty_logs = RiderDutyLog.objects.filter(
                rider=r, went_online__gte=start_dt, went_online__lte=end_dt
            )
            online_minutes = sum(d.duration_minutes or 0 for d in duty_logs)

            # Peak hour minutes
            peak_minutes = 0
            for d in duty_logs:
                if d.went_offline and d.went_online:
                    # Check overlap with 12-3pm and 5-8pm
                    on_hour = d.went_online.hour
                    off_hour = d.went_offline.hour if d.went_offline else on_hour
                    if (12 <= on_hour < 15) or (17 <= on_hour < 20):
                        peak_minutes += d.duration_minutes or 0
                    elif (12 <= off_hour < 15) or (17 <= off_hour < 20):
                        peak_minutes += (d.duration_minutes or 0) // 2

            # Calculate period days for online ratio
            period_days = max((end_dt - start_dt).days, 1)
            online_days_ratio = round(
                min(online_minutes / (period_days * 480), 1.0) * 100, 1  # 8hr workday
            )
            peak_hour_pct = (
                round(peak_minutes / max(online_minutes, 1) * 100, 1)
                if online_minutes
                else 0
            )

            result.append(
                {
                    "id": str(r.id),
                    "rider_id": r.rider_id,
                    "name": r.user.contact_name or r.user.get_full_name(),
                    "phone": r.user.phone,
                    "status": r.status,
                    "orders_completed": completed,
                    "orders_rejected": declined,
                    "orders_failed": failed,
                    "revenue": str(revenue),
                    "distance_km": str(distance),
                    "acceptance_rate": acceptance_rate,
                    "ghost_ride_flag": ghost_flag,
                    "peak_hour_pct": peak_hour_pct,
                    "csat": round(csat, 2) if csat else None,
                    "online_days_ratio": online_days_ratio,
                }
            )

        return Response(result)


class OCCZoneMerchantsView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request, pk):
        period = request.query_params.get("period", "this_month")
        start_dt, end_dt, _ = _parse_period(period)

        merchants = Merchant.objects.filter(zone_id=pk).select_related("user")
        result = []

        for m in merchants:
            # TODO: switch to snapshot table once populated
            orders_qs = _order_qs_for_period(start_dt, end_dt).filter(user=m.user)
            total_orders = orders_qs.count()
            completed = orders_qs.filter(status="Done").count()
            failed = orders_qs.filter(status="Failed").count()
            revenue = orders_qs.filter(status="Done").aggregate(
                rev=Coalesce(Sum("total_amount"), Decimal("0"))
            )["rev"]
            avg_order_value = (
                revenue / Decimal(str(completed)) if completed else Decimal("0")
            )
            fulfillment_rate = (
                round(completed / total_orders * 100, 1) if total_orders else 0
            )

            # Days since last order
            last_order = m.last_order_date
            days_since = (
                (timezone.now() - last_order).days if last_order else None
            )

            # Order frequency per day
            period_days = max((end_dt - start_dt).days, 1)
            freq = round(total_orders / period_days, 2)

            result.append(
                {
                    "id": str(m.id),
                    "merchant_id": m.merchant_id,
                    "name": m.user.business_name or "Unknown",
                    "contact": m.user.contact_name or "",
                    "phone": m.user.phone,
                    "activity_status": m.activity_status,
                    "total_orders": total_orders,
                    "orders_completed": completed,
                    "orders_failed": failed,
                    "revenue": str(revenue),
                    "avg_order_value": str(avg_order_value.quantize(Decimal("0.01"))),
                    "fulfillment_rate": fulfillment_rate,
                    "last_order_date": (
                        last_order.isoformat() if last_order else None
                    ),
                    "days_since_last_order": days_since,
                    "order_frequency_per_day": freq,
                }
            )

        return Response(result)


# ---------------------------------------------------------------------------
# Rider endpoints
# ---------------------------------------------------------------------------


class OCCRiderPerformanceView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request, pk):
        period = request.query_params.get("period", "this_month")
        start_dt, end_dt, _ = _parse_period(period)

        try:
            rider = Rider.objects.select_related("user", "vehicle_asset").get(pk=pk)
        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # TODO: switch to snapshot table once populated
        orders_qs = _order_qs_for_period(start_dt, end_dt).filter(rider=rider)
        completed = orders_qs.filter(status="Done").count()
        failed = orders_qs.filter(status="Failed").count()
        total = orders_qs.count()

        revenue = orders_qs.filter(status="Done").aggregate(
            rev=Coalesce(Sum("total_amount"), Decimal("0"))
        )["rev"]
        distance = orders_qs.filter(status="Done").aggregate(
            dist=Coalesce(Sum("distance_km"), Decimal("0"))
        )["dist"]

        avg_delivery_time = orders_qs.filter(status="Done").aggregate(
            avg_time=Avg("duration_minutes")
        )["avg_time"]

        # Acceptance rate
        from riders.models import OrderOffer

        offers = OrderOffer.objects.filter(
            rider=rider, created_at__gte=start_dt, created_at__lte=end_dt
        )
        total_offers = offers.count()
        declined = offers.filter(status="declined").count()
        acceptance_rate = (
            round((1 - declined / total_offers) * 100, 1) if total_offers else 100.0
        )

        # CSAT
        csat = DeliveryRating.objects.filter(
            rider=rider, created_at__gte=start_dt, created_at__lte=end_dt
        ).aggregate(avg=Avg("score"))["avg"]

        # KM to revenue ratio
        km_to_rev = (
            round(float(distance) / float(revenue), 4) if revenue else 0
        )

        # Revenue per KM
        rev_per_km = (
            round(float(revenue) / float(distance), 2) if distance else 0
        )

        # Failed delivery rate
        failed_rate = round(failed / total * 100, 1) if total else 0

        # Online/offline & peak hours
        duty_logs = RiderDutyLog.objects.filter(
            rider=rider, went_online__gte=start_dt, went_online__lte=end_dt
        )
        online_minutes = sum(d.duration_minutes or 0 for d in duty_logs)
        period_days = max((end_dt - start_dt).days, 1)
        online_vs_offline = round(
            min(online_minutes / (period_days * 480), 1.0) * 100, 1
        )

        # Peak hour utilisation
        peak_minutes = 0
        for d in duty_logs:
            if d.duration_minutes and d.went_online:
                h = d.went_online.hour
                if (12 <= h < 15) or (17 <= h < 20):
                    peak_minutes += d.duration_minutes
        peak_util = (
            round(peak_minutes / max(online_minutes, 1) * 100, 1)
            if online_minutes
            else 0
        )

        # Ghost ride
        ghost_ratio = 0
        if rider.vehicle_asset and rider.status == "offline":
            if float(rider.vehicle_asset.speed or 0) > 5:
                ghost_ratio = 100  # currently flagged

        # Anomaly flags
        anomalies = []
        if acceptance_rate < 70:
            anomalies.append(
                {
                    "metric": "acceptance_rate",
                    "severity": "CRITICAL" if acceptance_rate < 50 else "WARNING",
                    "message": f"Acceptance rate is {acceptance_rate}%",
                }
            )
        if ghost_ratio > 0:
            anomalies.append(
                {
                    "metric": "ghost_ride",
                    "severity": "CRITICAL",
                    "message": "Rider is offline but vehicle GPS shows movement",
                }
            )
        if csat and csat < 3.5:
            anomalies.append(
                {
                    "metric": "csat",
                    "severity": "WARNING",
                    "message": f"CSAT rating is {round(csat, 2)} (below 3.5)",
                }
            )
        if failed_rate > 10:
            anomalies.append(
                {
                    "metric": "failed_delivery_rate",
                    "severity": "WARNING",
                    "message": f"Failed delivery rate is {failed_rate}%",
                }
            )
        if peak_util < 40 and online_minutes > 60:
            anomalies.append(
                {
                    "metric": "peak_hour_utilisation",
                    "severity": "WARNING",
                    "message": f"Only {peak_util}% of online time during peak hours",
                }
            )

        return Response(
            {
                "rider_id": rider.rider_id,
                "name": rider.user.contact_name or rider.user.get_full_name(),
                "km_to_revenue_ratio": km_to_rev,
                "online_vs_offline_days": online_vs_offline,
                "acceptance_rate": acceptance_rate,
                "ghost_ride_ratio": ghost_ratio,
                "avg_delivery_time_minutes": (
                    round(avg_delivery_time, 1) if avg_delivery_time else None
                ),
                "csat_rating": round(csat, 2) if csat else None,
                "failed_delivery_rate": failed_rate,
                "peak_hour_utilisation": peak_util,
                "revenue_per_km": rev_per_km,
                "orders": {
                    "total": total,
                    "completed": completed,
                    "rejected": declined,
                    "failed": failed,
                },
                "revenue": str(revenue),
                "distance_km": str(distance),
                "anomaly_flags": anomalies,
            }
        )


class OCCRiderLocationsView(APIView):
    """Bulk GPS endpoint for map view — returns all rider locations."""

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request):
        riders = Rider.objects.filter(
            current_latitude__isnull=False,
            current_longitude__isnull=False,
        ).select_related("user", "home_zone")

        result = []
        for r in riders:
            result.append(
                {
                    "rider_id": r.rider_id,
                    "name": r.user.contact_name or r.user.get_full_name(),
                    "latitude": float(r.current_latitude),
                    "longitude": float(r.current_longitude),
                    "status": r.status,
                    "speed": float(r.current_speed or 0),
                    "is_moving": r.is_moving,
                    "last_updated": (
                        r.last_location_update.isoformat()
                        if r.last_location_update
                        else None
                    ),
                    "zone": r.home_zone.name if r.home_zone else None,
                }
            )

        return Response(result)


# ---------------------------------------------------------------------------
# Merchant endpoints
# ---------------------------------------------------------------------------


class OCCMerchantAnalyticsView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request, pk):
        period = request.query_params.get("period", "this_month")
        start_dt, end_dt, _ = _parse_period(period)

        try:
            merchant = Merchant.objects.select_related("user", "zone").get(pk=pk)
        except Merchant.DoesNotExist:
            return Response(
                {"error": "Merchant not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # TODO: switch to snapshot table once populated
        orders_qs = _order_qs_for_period(start_dt, end_dt).filter(user=merchant.user)
        total_orders = orders_qs.count()
        completed = orders_qs.filter(status="Done").count()
        failed = orders_qs.filter(status="Failed").count()
        revenue = orders_qs.filter(status="Done").aggregate(
            rev=Coalesce(Sum("total_amount"), Decimal("0"))
        )["rev"]
        avg_order_value = (
            revenue / Decimal(str(completed)) if completed else Decimal("0")
        )
        fulfillment_rate = (
            round(completed / total_orders * 100, 1) if total_orders else 0
        )
        period_days = max((end_dt - start_dt).days, 1)
        freq = round(total_orders / period_days, 2)

        days_since = None
        if merchant.last_order_date:
            days_since = (timezone.now() - merchant.last_order_date).days

        return Response(
            {
                "id": str(merchant.id),
                "merchant_id": merchant.merchant_id,
                "name": merchant.user.business_name or "Unknown",
                "total_orders": total_orders,
                "orders_completed": completed,
                "orders_failed": failed,
                "revenue": str(revenue),
                "avg_order_value": str(avg_order_value.quantize(Decimal("0.01"))),
                "fulfillment_rate": fulfillment_rate,
                "order_frequency_per_day": freq,
                "last_order_date": (
                    merchant.last_order_date.isoformat()
                    if merchant.last_order_date
                    else None
                ),
                "days_since_last_order": days_since,
                "activity_status": merchant.activity_status,
                "acquisition_date": merchant.user.created_at.isoformat(),
                "acquisition_source": merchant.acquisition_source,
                "zone": merchant.zone.name if merchant.zone else None,
            }
        )


# ---------------------------------------------------------------------------
# Leaderboard endpoints
# ---------------------------------------------------------------------------


class OCCZoneLeaderboardView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request):
        period = request.query_params.get("period", "this_month")
        start_dt, end_dt, _ = _parse_period(period)

        zones = Zone.objects.filter(is_active=True).select_related("vertical")
        entries = []

        for z in zones:
            rider_ids = list(
                Rider.objects.filter(home_zone=z).values_list("id", flat=True)
            )

            # TODO: switch to snapshot table once populated
            orders_qs = _order_qs_for_period(start_dt, end_dt).filter(
                rider_id__in=rider_ids
            )
            agg = orders_qs.aggregate(
                orders=Count("id", filter=Q(status="Done")),
                revenue=Coalesce(
                    Sum("total_amount", filter=Q(status="Done")), Decimal("0")
                ),
            )

            # Zone target
            target_rev = Decimal("600000")
            try:
                zt = ZoneTarget.objects.get(
                    zone=z,
                    month__year=start_dt.year,
                    month__month=start_dt.month,
                )
                target_rev = _scale_target(zt.target_revenue, period)
            except ZoneTarget.DoesNotExist:
                target_rev = _scale_target(target_rev, period)

            target_pct = (
                round(float(agg["revenue"]) / float(target_rev) * 100, 1)
                if target_rev
                else 0
            )

            # Captain info and earnings
            captain_name = None
            try:
                zc = ZoneCaptain.objects.select_related("user").get(
                    zone=z, is_active=True
                )
                captain_name = zc.user.contact_name or zc.user.get_full_name()
            except ZoneCaptain.DoesNotExist:
                pass

            # Zone captain salary: 50k base + 40k transport + 4% gross rev
            rev = agg["revenue"]
            earnings = {
                "base": "50000",
                "transport": "40000",
                "commission": str((rev * Decimal("0.04")).quantize(Decimal("0.01"))),
                "total": str(
                    (Decimal("90000") + rev * Decimal("0.04")).quantize(Decimal("0.01"))
                ),
            }

            vertical_code = z.vertical.code if z.vertical else ""
            entries.append(
                {
                    "zone_id": str(z.id),
                    "zone_name": z.name,
                    "vertical": z.vertical.name if z.vertical else None,
                    "vertical_id": str(z.vertical.id) if z.vertical else None,
                    "color": VERTICAL_COLORS.get(vertical_code, "#6B7280"),
                    "captain": captain_name,
                    "orders": agg["orders"],
                    "revenue": str(rev),
                    "target": round(float(target_rev)),
                    "target_pct": target_pct,
                    "earnings": earnings,
                }
            )

        # Sort by revenue descending
        entries.sort(key=lambda x: float(x["revenue"]), reverse=True)
        for i, e in enumerate(entries):
            e["rank"] = i + 1

        return Response(entries)


class OCCVerticalLeaderboardView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request):
        period = request.query_params.get("period", "this_month")
        start_dt, end_dt, _ = _parse_period(period)

        verticals = Vertical.objects.filter(is_active=True).prefetch_related("zones")
        entries = []

        for v in verticals:
            zone_ids = list(v.zones.filter(is_active=True).values_list("id", flat=True))
            rider_ids = list(
                Rider.objects.filter(home_zone_id__in=zone_ids).values_list(
                    "id", flat=True
                )
            )

            # TODO: switch to snapshot table once populated
            orders_qs = _order_qs_for_period(start_dt, end_dt).filter(
                rider_id__in=rider_ids
            )
            agg = orders_qs.aggregate(
                orders=Count("id", filter=Q(status="Done")),
                revenue=Coalesce(
                    Sum("total_amount", filter=Q(status="Done")), Decimal("0")
                ),
            )

            # Target
            targets = ZoneTarget.objects.filter(
                zone_id__in=zone_ids,
                month__year=start_dt.year,
                month__month=start_dt.month,
            )
            total_target_rev = sum(
                _scale_target(t.target_revenue, period) for t in targets
            ) or Decimal("1")
            target_pct = round(
                float(agg["revenue"]) / float(total_target_rev) * 100, 1
            )

            # Vertical lead salary: 250k base + 80k transport + 1.1% gross rev
            rev = agg["revenue"]
            earnings = {
                "base": "250000",
                "transport": "80000",
                "commission": str(
                    (rev * Decimal("0.011")).quantize(Decimal("0.01"))
                ),
                "total": str(
                    (Decimal("330000") + rev * Decimal("0.011")).quantize(
                        Decimal("0.01")
                    )
                ),
            }

            entries.append(
                {
                    "vertical_id": str(v.id),
                    "name": v.name,
                    "lead_name": v.lead_name,
                    "orders": agg["orders"],
                    "revenue": str(rev),
                    "target_pct": target_pct,
                    "earnings": earnings,
                }
            )

        entries.sort(key=lambda x: float(x["revenue"]), reverse=True)
        for i, e in enumerate(entries):
            e["rank"] = i + 1

        return Response(entries)


# ---------------------------------------------------------------------------
# Order analytics
# ---------------------------------------------------------------------------


class OCCOrderAnalyticsView(APIView):
    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOCCReadScope]

    def get(self, request):
        period = request.query_params.get("period", "this_month")
        zone_id = request.query_params.get("zone")
        vertical_id = request.query_params.get("vertical")
        start_dt, end_dt, _ = _parse_period(period)

        # TODO: switch to snapshot table once populated
        orders_qs = _order_qs_for_period(start_dt, end_dt)

        # Scope to zone or vertical
        if zone_id:
            rider_ids = Rider.objects.filter(home_zone_id=zone_id).values_list(
                "id", flat=True
            )
            orders_qs = orders_qs.filter(rider_id__in=rider_ids)
        elif vertical_id:
            zone_ids = Zone.objects.filter(vertical_id=vertical_id).values_list(
                "id", flat=True
            )
            rider_ids = Rider.objects.filter(home_zone_id__in=zone_ids).values_list(
                "id", flat=True
            )
            orders_qs = orders_qs.filter(rider_id__in=rider_ids)

        agg = orders_qs.aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(status="Done")),
            failed=Count("id", filter=Q(status="Failed")),
            canceled=Count(
                "id", filter=Q(status__in=["CustomerCanceled", "RiderCanceled"])
            ),
            pending=Count("id", filter=Q(status="Pending")),
            revenue=Coalesce(
                Sum("total_amount", filter=Q(status="Done")), Decimal("0")
            ),
            avg_delivery_fee=Coalesce(
                Avg("total_amount", filter=Q(status="Done")),
                Decimal("0"),
                output_field=models.DecimalField(),
            ),
            avg_distance_km=Coalesce(
                Avg("distance_km", filter=Q(status="Done")),
                Decimal("0"),
                output_field=models.DecimalField(),
            ),
            avg_delivery_time_minutes=Coalesce(
                Avg("duration_minutes", filter=Q(status="Done")),
                0,
                output_field=models.FloatField(),
            ),
        )

        # By zone
        by_zone = []
        zone_aggs = (
            orders_qs.filter(rider__home_zone__isnull=False)
            .values("rider__home_zone__id", "rider__home_zone__name")
            .annotate(
                orders=Count("id", filter=Q(status="Done")),
                revenue=Coalesce(
                    Sum("total_amount", filter=Q(status="Done")), Decimal("0")
                ),
            )
            .order_by("-revenue")
        )
        for za in zone_aggs:
            by_zone.append(
                {
                    "zone_id": str(za["rider__home_zone__id"]),
                    "zone_name": za["rider__home_zone__name"],
                    "orders": za["orders"],
                    "revenue": str(za["revenue"]),
                }
            )

        # By hour
        by_hour = (
            orders_qs.annotate(hour=ExtractHour("created_at"))
            .values("hour")
            .annotate(orders=Count("id"))
            .order_by("hour")
        )
        by_hour_list = [{"hour": h["hour"], "orders": h["orders"]} for h in by_hour]

        return Response(
            {
                "total": agg["total"],
                "completed": agg["completed"],
                "failed": agg["failed"],
                "canceled": agg["canceled"],
                "pending": agg["pending"],
                "revenue": str(agg["revenue"]),
                "avg_delivery_fee": str(
                    agg["avg_delivery_fee"].quantize(Decimal("0.01"))
                    if isinstance(agg["avg_delivery_fee"], Decimal)
                    else agg["avg_delivery_fee"]
                ),
                "avg_distance_km": str(
                    agg["avg_distance_km"].quantize(Decimal("0.01"))
                    if isinstance(agg["avg_distance_km"], Decimal)
                    else agg["avg_distance_km"]
                ),
                "avg_delivery_time_minutes": agg["avg_delivery_time_minutes"],
                "by_zone": by_zone,
                "by_hour": by_hour_list,
            }
        )


# ---------------------------------------------------------------------------
# Zone Target management (CRUD)
# ---------------------------------------------------------------------------


class OCCZoneTargetListCreateView(APIView):
    """
    GET  — List zone targets, filterable by ?zone=<uuid>&month=YYYY-MM-DD
    POST — Create a new zone target.
    """

    authentication_classes = [ServiceAPIKeyAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            return [HasOCCReadScope()]
        return [HasOCCWriteScope()]

    def get(self, request):
        qs = ZoneTarget.objects.select_related("zone").all()

        zone_id = request.query_params.get("zone")
        if zone_id:
            qs = qs.filter(zone_id=zone_id)

        month = request.query_params.get("month")
        if month:
            try:
                from datetime import datetime as dt

                parsed = dt.strptime(month, "%Y-%m-%d").date().replace(day=1)
                qs = qs.filter(month=parsed)
            except ValueError:
                pass

        data = [
            {
                "id": str(t.id),
                "zone": str(t.zone_id),
                "zone_name": t.zone.name,
                "month": t.month.isoformat(),
                "target_orders": t.target_orders,
                "target_revenue": str(t.target_revenue),
            }
            for t in qs
        ]
        return Response(data)

    def post(self, request):
        from .serializers import ZoneTargetSerializer

        serializer = ZoneTargetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OCCZoneTargetDetailView(APIView):
    """
    GET    — Retrieve a single zone target.
    PUT    — Full update of a zone target.
    PATCH  — Partial update of a zone target.
    DELETE — Delete a zone target.
    """

    authentication_classes = [ServiceAPIKeyAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            return [HasOCCReadScope()]
        return [HasOCCWriteScope()]

    def _get_object(self, pk):
        try:
            return ZoneTarget.objects.select_related("zone").get(pk=pk)
        except ZoneTarget.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )
        from .serializers import ZoneTargetSerializer

        return Response(ZoneTargetSerializer(obj).data)

    def put(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )
        from .serializers import ZoneTargetSerializer

        serializer = ZoneTargetSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )
        from .serializers import ZoneTargetSerializer

        serializer = ZoneTargetSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
