"""URL routes for the Operations Dashboard app (mounted at /api/ops/)."""

from django.urls import path

from .views import (
    OpsAlertDashboardView,
    OpsAlertDetailView,
    OpsAlertGenerateView,
    OpsAlertListView,
    OpsAlertResolveView,
    OpsAlertRuleDetailView,
    OpsAlertRuleListView,
    OpsCodDashboardView,
    OpsCodOrdersView,
    OpsFuelDashboardView,
    OpsFuelUploadView,
    OpsHealthView,
    OpsOrderDashboardView,
    OpsOrderListView,
    OpsPaymentOrdersView,
    OpsPaymentsView,
    OpsTrackingDashboardView,
)

urlpatterns = [
    path("health/", OpsHealthView.as_view(), name="ops-health"),
    # Alerts (Phase 4)
    path("alerts/", OpsAlertListView.as_view(), name="ops-alert-list"),
    path(
        "alerts/generate/",
        OpsAlertGenerateView.as_view(),
        name="ops-alert-generate",
    ),
    path(
        "alerts/<uuid:pk>/",
        OpsAlertDetailView.as_view(),
        name="ops-alert-detail",
    ),
    path(
        "alerts/<uuid:pk>/resolve/",
        OpsAlertResolveView.as_view(),
        name="ops-alert-resolve",
    ),
    # Alert dashboard + rules (Phase 5, alert side)
    path(
        "alert-dashboard/",
        OpsAlertDashboardView.as_view(),
        name="ops-alert-dashboard",
    ),
    path(
        "alert-rules/",
        OpsAlertRuleListView.as_view(),
        name="ops-alert-rule-list",
    ),
    path(
        "alert-rules/<uuid:pk>/",
        OpsAlertRuleDetailView.as_view(),
        name="ops-alert-rule-detail",
    ),
    # Consolidated order metrics + live rider/vehicle tracking
    path(
        "order-dashboard/",
        OpsOrderDashboardView.as_view(),
        name="ops-order-dashboard",
    ),
    path(
        "order-dashboard/orders/",
        OpsOrderListView.as_view(),
        name="ops-order-list",
    ),
    path(
        "tracking-dashboard/",
        OpsTrackingDashboardView.as_view(),
        name="ops-tracking-dashboard",
    ),
    # Payments + COD dashboards (Phase 5, money side / Phase 2 metrics)
    path("payments/", OpsPaymentsView.as_view(), name="ops-payments"),
    path(
        "payments/orders/",
        OpsPaymentOrdersView.as_view(),
        name="ops-payment-orders",
    ),
    path(
        "cod-dashboard/",
        OpsCodDashboardView.as_view(),
        name="ops-cod-dashboard",
    ),
    path(
        "cod-dashboard/orders/",
        OpsCodOrdersView.as_view(),
        name="ops-cod-orders",
    ),
    # Fuel tracking (upload daily bills + stats)
    path("fuel/upload/", OpsFuelUploadView.as_view(), name="ops-fuel-upload"),
    path(
        "fuel-dashboard/",
        OpsFuelDashboardView.as_view(),
        name="ops-fuel-dashboard",
    ),
    # Later phase (guide §14.9): financial-dashboard/ (cost tabs out of scope).
]
