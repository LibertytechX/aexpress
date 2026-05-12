from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from dispatcher.models import Rider, Vertical, Zone

from . import services


class OperationsBaseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_scope(self):
        return services.get_scope(self.request.user)

    def get_period(self):
        return self.request.query_params.get("period", "this_month")


class OperationsMeView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        return Response(services.scope_payload(request.user, scope))


class DashboardSummaryView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        return Response(services.dashboard_summary(scope, self.get_period()))


class DashboardFlagsView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        limit = int(request.query_params.get("limit", 50))
        return Response({"results": services.build_flags(scope, limit=limit)})


class VerticalListView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        period = self.get_period()
        start_dt, end_dt = services.parse_period(period)
        rows = [
            services.vertical_summary(vertical, scope, start_dt, end_dt)
            for vertical in services.scoped_verticals(scope).prefetch_related("zones")
        ]
        return Response({"period": period, "results": rows})


class VerticalDetailView(OperationsBaseView):
    def get(self, request, pk):
        scope = self.get_scope()
        period = self.get_period()
        start_dt, end_dt = services.parse_period(period)
        vertical = get_object_or_404(Vertical, pk=pk)
        services.ensure_vertical_allowed(scope, vertical)
        payload = services.vertical_summary(vertical, scope, start_dt, end_dt)
        zones = [
            services.zone_summary(zone, scope, start_dt, end_dt)
            for zone in vertical.zones.filter(is_active=True).select_related("vertical")
            if scope.is_global or zone.id in scope.zone_ids
        ]
        payload["zones"] = zones
        return Response(payload)


class VerticalZonesView(OperationsBaseView):
    def get(self, request, pk):
        scope = self.get_scope()
        period = self.get_period()
        start_dt, end_dt = services.parse_period(period)
        vertical = get_object_or_404(Vertical, pk=pk)
        services.ensure_vertical_allowed(scope, vertical)
        rows = [
            services.zone_summary(zone, scope, start_dt, end_dt)
            for zone in vertical.zones.filter(is_active=True).select_related("vertical")
            if scope.is_global or zone.id in scope.zone_ids
        ]
        return Response({"period": period, "results": rows})


class ZoneListView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        period = self.get_period()
        start_dt, end_dt = services.parse_period(period)
        rows = [
            services.zone_summary(zone, scope, start_dt, end_dt)
            for zone in services.scoped_zones(scope)
        ]
        return Response({"period": period, "results": rows})


class ZoneDetailView(OperationsBaseView):
    def get(self, request, pk):
        scope = self.get_scope()
        period = self.get_period()
        start_dt, end_dt = services.parse_period(period)
        zone = get_object_or_404(Zone.objects.select_related("vertical"), pk=pk)
        return Response(services.zone_summary(zone, scope, start_dt, end_dt, include_nested=True))


class ZoneRidersView(OperationsBaseView):
    def get(self, request, pk):
        scope = self.get_scope()
        period = self.get_period()
        start_dt, end_dt = services.parse_period(period)
        zone = get_object_or_404(Zone, pk=pk)
        services.ensure_zone_allowed(scope, zone)
        riders = Rider.objects.filter(hub__zone=zone).select_related(
            "user", "hub", "hub__zone", "vehicle_asset"
        )
        return Response(
            {
                "period": period,
                "zone_id": str(zone.id),
                "results": [
                    services.rider_summary(rider, start_dt, end_dt) for rider in riders
                ],
            }
        )


class RiderDetailView(OperationsBaseView):
    def get(self, request, pk):
        scope = self.get_scope()
        start_dt, end_dt = services.parse_period(self.get_period())
        rider = get_object_or_404(
            Rider.objects.select_related("user", "hub", "hub__zone", "vehicle_asset"),
            pk=pk,
        )
        services.ensure_rider_allowed(scope, rider)
        return Response(services.rider_summary(rider, start_dt, end_dt))


class RiderPerformanceView(RiderDetailView):
    pass


class RiderDailyActivityView(OperationsBaseView):
    def get(self, request, pk):
        scope = self.get_scope()
        period = self.get_period()
        start_dt, end_dt = services.parse_period(period)
        rider = get_object_or_404(Rider.objects.select_related("user", "hub", "hub__zone"), pk=pk)
        services.ensure_rider_allowed(scope, rider)
        return Response(
            {
                "period": period,
                "rider_id": str(rider.id),
                "results": services.rider_daily_activity(rider, start_dt, end_dt),
            }
        )


class LeaderboardsView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        return Response(services.leaderboard(scope, self.get_period()))


class OrdersListView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        return Response(
            services.orders_list(scope, self.get_period(), request.query_params)
        )


class OrdersAnalyticsView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        return Response(services.orders_analytics(scope, self.get_period()))


class MerchantsListView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        return Response(
            services.merchants_list(scope, self.get_period(), request.query_params)
        )


class JumiaHubsListView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        return Response(
            services.hubs_list(scope, self.get_period(), request.query_params)
        )


class VehiclesListView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        return Response(services.vehicles_list(scope, request.query_params))


class RiderVehicleView(OperationsBaseView):
    def get(self, request, pk):
        scope = self.get_scope()
        rider = get_object_or_404(
            Rider.objects.select_related("user", "hub", "hub__zone", "vehicle_asset"),
            pk=pk,
        )
        return Response(services.rider_vehicle(scope, rider))


class KmVisibilityView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        return Response(services.km_visibility(scope))


class KmIntegrityView(OperationsBaseView):
    def get(self, request):
        scope = self.get_scope()
        return Response(services.km_integrity(scope, request.query_params))
