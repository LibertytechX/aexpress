"""
Operations Dashboard endpoints (mounted at /api/ops/).

Phase 4 ships the alert endpoints (list / detail / resolve / generate) on top of
the Phase 1 health endpoint. Dashboard/metrics endpoints arrive in later phases.

Response envelope convention (use everywhere in this app):
    { "success": bool, "data": <obj|list>, "date_range": {filter, start, end} | None }
"""

import math

from django.db.models import Count, Q
from rest_framework import status as http_status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from dispatcher.authentication import ServiceAPIKeyAuthentication
from dispatcher.periods import _parse_period

from .filters import parse_filter
from .models import OPEN_ALERT_STATUSES, Alert, AlertRule, AlertStatus
from .permissions import HasOpsReadScope, HasOpsWriteScope
from .serializers import AlertRuleSerializer, AlertSerializer


def _pct(part, whole):
    """Percentage helper (whole == 0 → 0.0)."""
    return round(part / whole * 100, 1) if whole else 0.0


def ops_response(data, *, success=True, period=None, date_range=None, **extra):
    """Standard envelope for all ops endpoints.

    Pass `date_range` (descriptor from filters.parse_filter) for the general
    dashboard filter, or `period` for the simple period-only helper.
    """
    if date_range is None and period is not None:
        start_dt, end_dt, _ = _parse_period(period)
        date_range = {
            "filter": period,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
        }
    payload = {"success": success, "data": data, "date_range": date_range}
    payload.update(extra)
    return Response(payload)


def _paginate(request, qs, default_size=25, max_size=100):
    """Slice a queryset and return (items, meta) for the envelope."""
    try:
        page = max(int(request.query_params.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.query_params.get("page_size", default_size))
    except (TypeError, ValueError):
        page_size = default_size
    page_size = max(1, min(page_size, max_size))

    count = qs.count()
    total_pages = max(math.ceil(count / page_size), 1)
    start = (page - 1) * page_size
    items = list(qs[start : start + page_size])
    meta = {
        "count": count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
    return items, meta


class OpsHealthView(APIView):
    """GET /api/ops/health/ — confirms the app is wired and auth works."""

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOpsReadScope]

    def get(self, request):
        period = request.query_params.get("period", "this_month")
        return ops_response(
            {"app": "oprtn_dashboard", "status": "ok", "phase": 4},
            period=period,
        )


class OpsAlertListView(APIView):
    """
    GET /api/ops/alerts/ — list alerts.

    Filters: ?status (default `active` = new+investigating; `all` for everything),
    ?type (alert_type), ?severity, ?entity_type, plus ?page & ?page_size.
    """

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOpsReadScope]

    def get(self, request):
        qs = Alert.objects.select_related(
            "rider", "order", "merchant", "vehicle", "zone"
        )

        status_param = request.query_params.get("status", "active")
        if status_param == "active":
            qs = qs.filter(status__in=OPEN_ALERT_STATUSES)
        elif status_param and status_param != "all":
            qs = qs.filter(status=status_param)

        alert_type = request.query_params.get("type")
        if alert_type:
            qs = qs.filter(alert_type=alert_type)

        severity = request.query_params.get("severity")
        if severity:
            qs = qs.filter(severity=severity)

        entity_type = request.query_params.get("entity_type")
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        items, meta = _paginate(request, qs)
        data = {"results": AlertSerializer(items, many=True).data, **meta}
        return ops_response(data)


class OpsAlertDetailView(APIView):
    """GET /api/ops/alerts/<uuid>/ — single alert."""

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOpsReadScope]

    def get(self, request, pk):
        try:
            alert = Alert.objects.select_related(
                "rider", "order", "merchant", "vehicle", "zone"
            ).get(pk=pk)
        except Alert.DoesNotExist:
            return Response(
                {"success": False, "detail": "Not found."},
                status=http_status.HTTP_404_NOT_FOUND,
            )
        return ops_response(AlertSerializer(alert).data)


class OpsAlertResolveView(APIView):
    """
    POST/PATCH /api/ops/alerts/<uuid>/resolve/ — change an alert's status.

    Body: { "status": "resolved" | "false_positive" | "investigating",
            "resolution_note": "..." }  (default status = resolved)
    """

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOpsWriteScope]

    def _update(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response(
                {"success": False, "detail": "Not found."},
                status=http_status.HTTP_404_NOT_FOUND,
            )

        target = request.data.get("status", AlertStatus.RESOLVED)
        note = request.data.get("resolution_note", "")
        valid = {
            AlertStatus.RESOLVED,
            AlertStatus.FALSE_POSITIVE,
            AlertStatus.INVESTIGATING,
        }
        if target not in valid:
            return Response(
                {"success": False, "detail": f"Invalid status '{target}'."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        if target == AlertStatus.INVESTIGATING:
            alert.status = AlertStatus.INVESTIGATING
            alert.save(update_fields=["status", "updated_at"])
        else:
            alert.resolve(
                note=note, false_positive=(target == AlertStatus.FALSE_POSITIVE)
            )

        return ops_response(AlertSerializer(alert).data)

    def post(self, request, pk):
        return self._update(request, pk)

    def patch(self, request, pk):
        return self._update(request, pk)


class OpsAlertGenerateView(APIView):
    """
    POST /api/ops/alerts/generate/ — run the alert engine synchronously.

    Body (optional): { "types": ["BIKE_AFTER_HOURS", ...] } to limit the run.
    """

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOpsWriteScope]

    def post(self, request):
        from .alerts.engine import run_all_rules

        only_types = request.data.get("types") or None
        summary = run_all_rules(only_types=only_types)
        return ops_response(summary)


class OpsAlertDashboardView(APIView):
    """
    GET /api/ops/alert-dashboard/?period= — alert summaries.

    Returns: a period summary (alerts created in the period, by status/severity,
    resolution rate, by type), the all-time **active** picture (open alerts by
    severity/type, regardless of date), and a recent-active list.
    """

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOpsReadScope]

    def get(self, request):
        start_dt, end_dt, desc = parse_filter(request)
        try:
            limit = min(max(int(request.query_params.get("limit", 20)), 1), 100)
        except (TypeError, ValueError):
            limit = 20

        # ── Period summary (one aggregate) ──────────────────────────
        period_qs = Alert.objects.filter(
            created_at__gte=start_dt, created_at__lte=end_dt
        )
        agg = period_qs.aggregate(
            total=Count("id"),
            new=Count("id", filter=Q(status=AlertStatus.NEW)),
            investigating=Count(
                "id", filter=Q(status=AlertStatus.INVESTIGATING)
            ),
            resolved=Count("id", filter=Q(status=AlertStatus.RESOLVED)),
            false_positive=Count(
                "id", filter=Q(status=AlertStatus.FALSE_POSITIVE)
            ),
            critical=Count("id", filter=Q(severity="critical")),
            high=Count("id", filter=Q(severity="high")),
            medium=Count("id", filter=Q(severity="medium")),
            low=Count("id", filter=Q(severity="low")),
        )
        closed = agg["resolved"] + agg["false_positive"]
        period_summary = {
            "total": agg["total"],
            "by_status": {
                "new": agg["new"],
                "investigating": agg["investigating"],
                "resolved": agg["resolved"],
                "false_positive": agg["false_positive"],
            },
            "by_severity": {
                "critical": agg["critical"],
                "high": agg["high"],
                "medium": agg["medium"],
                "low": agg["low"],
            },
            "resolution_rate": _pct(closed, agg["total"]),
        }
        period_by_type = list(
            period_qs.values("alert_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # ── All-time active picture ─────────────────────────────────
        active_qs = Alert.objects.filter(status__in=OPEN_ALERT_STATUSES)
        active_agg = active_qs.aggregate(
            total=Count("id"),
            critical=Count("id", filter=Q(severity="critical")),
            high=Count("id", filter=Q(severity="high")),
            medium=Count("id", filter=Q(severity="medium")),
            low=Count("id", filter=Q(severity="low")),
        )
        active_by_type = list(
            active_qs.values("alert_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        recent_active = active_qs.select_related(
            "rider", "order", "merchant", "vehicle", "zone"
        ).order_by("-last_seen_at")[:limit]

        data = {
            "period_summary": period_summary,
            "period_by_type": period_by_type,
            "active": {
                "total": active_agg["total"],
                "by_severity": {
                    "critical": active_agg["critical"],
                    "high": active_agg["high"],
                    "medium": active_agg["medium"],
                    "low": active_agg["low"],
                },
                "by_type": active_by_type,
            },
            "recent_active": AlertSerializer(recent_active, many=True).data,
        }
        return ops_response(data, date_range=desc)


class OpsAlertRuleListView(APIView):
    """GET /api/ops/alert-rules/ — list all alert rules (thresholds)."""

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOpsReadScope]

    def get(self, request):
        qs = AlertRule.objects.all()
        enabled = request.query_params.get("is_enabled")
        if enabled in ("true", "false"):
            qs = qs.filter(is_enabled=(enabled == "true"))
        return ops_response(AlertRuleSerializer(qs, many=True).data)


class OpsAlertRuleDetailView(APIView):
    """
    GET/PUT/PATCH /api/ops/alert-rules/<uuid>/ — view or edit a rule's
    thresholds. Writes require the ops write scope.
    """

    authentication_classes = [ServiceAPIKeyAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            return [HasOpsReadScope()]
        return [HasOpsWriteScope()]

    def _get(self, pk):
        try:
            return AlertRule.objects.get(pk=pk)
        except AlertRule.DoesNotExist:
            return None

    def get(self, request, pk):
        rule = self._get(pk)
        if not rule:
            return Response(
                {"success": False, "detail": "Not found."},
                status=http_status.HTTP_404_NOT_FOUND,
            )
        return ops_response(AlertRuleSerializer(rule).data)

    def _update(self, request, pk, partial):
        rule = self._get(pk)
        if not rule:
            return Response(
                {"success": False, "detail": "Not found."},
                status=http_status.HTTP_404_NOT_FOUND,
            )
        serializer = AlertRuleSerializer(rule, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return ops_response(serializer.data)
        return Response(
            {"success": False, "errors": serializer.errors},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)


class OpsPaymentsView(APIView):
    """
    GET /api/ops/payments/?period= — order amount across ALL payment types.

    Returns total order amount, recognized revenue, breakdown by payment method
    and status, and a cash-flow collection-timing split (§14.5).
    """

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOpsReadScope]

    def get(self, request):
        from orders.models import Order

        from .metrics import payment_metrics

        start_dt, end_dt, desc = parse_filter(request)
        qs = Order.objects.filter(
            created_at__gte=start_dt, created_at__lte=end_dt
        )
        return ops_response(
            payment_metrics.payment_breakdown(qs), date_range=desc
        )


class OpsCodDashboardView(APIView):
    """
    GET /api/ops/cod-dashboard/?period= — COD goods value, COD fee (separate
    from order amount), collection reconciliation, ageing, and top rider/merchant
    COD (§14.6).
    """

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOpsReadScope]

    def get(self, request):
        from orders.models import Order

        from .metrics import cod_metrics

        start_dt, end_dt, desc = parse_filter(request)
        qs = Order.objects.filter(
            created_at__gte=start_dt, created_at__lte=end_dt
        )
        return ops_response(cod_metrics.cod_dashboard(qs), date_range=desc)


class OpsFuelUploadView(APIView):
    """
    POST /api/ops/fuel/upload/ — upload the daily fuel bills .xlsx.

    Multipart field `file`. Rows are upserted by "Invoice number" (idempotent),
    linked to the fleet vehicle/rider by plate. Returns an import summary.
    """

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOpsWriteScope]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        from .fuel_import import import_fuel_workbook

        f = request.FILES.get("file")
        if not f:
            return Response(
                {"success": False, "detail": "No file uploaded (field 'file')."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        if not (f.name or "").lower().endswith((".xlsx", ".xlsm")):
            return Response(
                {"success": False, "detail": "Upload an .xlsx file."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        try:
            summary = import_fuel_workbook(f)
        except ValueError as exc:
            return Response(
                {"success": False, "detail": str(exc)},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        return ops_response(summary)


class OpsFuelDashboardView(APIView):
    """
    GET /api/ops/fuel-dashboard/ — fuel spend stats from imported bills.

    Honours the general dashboard filter (filtered on FuelBill.bill_date).
    """

    authentication_classes = [ServiceAPIKeyAuthentication]
    permission_classes = [HasOpsReadScope]

    def get(self, request):
        from .metrics import fuel_metrics
        from .models import FuelBill

        start_dt, end_dt, desc = parse_filter(request)
        qs = FuelBill.objects.filter(
            bill_date__gte=start_dt.date(), bill_date__lte=end_dt.date()
        )
        return ops_response(fuel_metrics.fuel_dashboard(qs), date_range=desc)
