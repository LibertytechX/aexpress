from django.urls import path

from .occ_views import (
    OCCMerchantAnalyticsView,
    OCCOrderAnalyticsView,
    OCCRiderLocationsView,
    OCCRiderPerformanceView,
    OCCVerticalDetailView,
    OCCVerticalLeaderboardView,
    OCCVerticalListView,
    OCCVerticalZonesView,
    OCCZoneDashboardView,
    OCCZoneLeaderboardView,
    OCCZoneMerchantsView,
    OCCZoneRidersView,
    OCCZoneTargetDetailView,
    OCCZoneTargetListCreateView,
)

urlpatterns = [
    # Verticals
    path("verticals/", OCCVerticalListView.as_view(), name="occ-vertical-list"),
    path("verticals/<uuid:pk>/", OCCVerticalDetailView.as_view(), name="occ-vertical-detail"),
    path("verticals/<uuid:pk>/zones/", OCCVerticalZonesView.as_view(), name="occ-vertical-zones"),
    # Zones
    path("zones/<uuid:pk>/dashboard/", OCCZoneDashboardView.as_view(), name="occ-zone-dashboard"),
    path("zones/<uuid:pk>/riders/", OCCZoneRidersView.as_view(), name="occ-zone-riders"),
    path("zones/<uuid:pk>/merchants/", OCCZoneMerchantsView.as_view(), name="occ-zone-merchants"),
    # Riders
    path("riders/<uuid:pk>/performance/", OCCRiderPerformanceView.as_view(), name="occ-rider-performance"),
    path("riders/locations/", OCCRiderLocationsView.as_view(), name="occ-rider-locations"),
    # Merchants
    path("merchants/<uuid:pk>/analytics/", OCCMerchantAnalyticsView.as_view(), name="occ-merchant-analytics"),
    # Leaderboards
    path("leaderboard/zones/", OCCZoneLeaderboardView.as_view(), name="occ-leaderboard-zones"),
    path("leaderboard/verticals/", OCCVerticalLeaderboardView.as_view(), name="occ-leaderboard-verticals"),
    # Orders
    path("orders/analytics/", OCCOrderAnalyticsView.as_view(), name="occ-order-analytics"),
    # Zone Targets
    path("zone-targets/", OCCZoneTargetListCreateView.as_view(), name="occ-zone-target-list"),
    path("zone-targets/<uuid:pk>/", OCCZoneTargetDetailView.as_view(), name="occ-zone-target-detail"),
]
