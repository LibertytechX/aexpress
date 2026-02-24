from django.urls import path
from .views import (
    VehicleListView,
    QuickSendView,
    MultiDropView,
    BulkImportView,
    OrderListView,
    OrderDetailView,
    OrderStatsView,
    CancelOrderView,
    CancelableOrdersView,
    CalculateFareView,
    VehicleUpdateView,
    AssignedOrdersView,
    AssignedOrderDetailView,
    AssignedRoutesView,
    OrderPickupView,
    cancel_order,
    DeliveryStartView,
    DeliveryCompleteView,
)
from .escrow_views import (
    ReleaseEscrowView,
    RefundEscrowView,
    EscrowStatusView,
    EscrowHistoryView,
)

app_name = "orders"

urlpatterns = [
    # Vehicle endpoints
    path("vehicles/", VehicleListView.as_view(), name="vehicle_list"),
    path("vehicles/<int:id>/", VehicleUpdateView.as_view(), name="vehicle_update"),
    # Order creation endpoints
    path("quick-send/", QuickSendView.as_view(), name="quick_send"),
    path("multi-drop/", MultiDropView.as_view(), name="multi_drop"),
    path("bulk-import/", BulkImportView.as_view(), name="bulk_import"),
    path("calculate-fare/", CalculateFareView.as_view(), name="calculate_fare"),
    # Order management endpoints
    path("", OrderListView.as_view(), name="order_list"),
    path("assigned/", AssignedOrdersView.as_view(), name="assigned_orders"),
    path(
        "assigned/<str:order_number>/",
        AssignedOrderDetailView.as_view(),
        name="assigned_order_detail",
    ),
    path("assigned-routes/", AssignedRoutesView.as_view(), name="assigned_routes"),
    path("pickup/", OrderPickupView.as_view(), name="order_pickup"),
    path(
        "delivery/<uuid:delivery_id>/start/",
        DeliveryStartView.as_view(),
        name="delivery_start",
    ),
    path(
        "delivery/<uuid:delivery_id>/deliver/",
        DeliveryCompleteView.as_view(),
        name="delivery_deliver",
    ),
    path("stats/", OrderStatsView.as_view(), name="order_stats"),
    # Escrow management endpoints
    path("escrow-history/", EscrowHistoryView.as_view(), name="escrow_history"),
    path("cancelable/", CancelableOrdersView.as_view(), name="cancelable_orders"),
    # Order-specific endpoints (using /action/order_number pattern)
    path(
        "release-escrow/<str:order_number>/",
        ReleaseEscrowView.as_view(),
        name="release_escrow",
    ),
    path(
        "refund-escrow/<str:order_number>/",
        RefundEscrowView.as_view(),
        name="refund_escrow",
    ),
    path(
        "escrow-status/<str:order_number>/",
        EscrowStatusView.as_view(),
        name="escrow_status",
    ),
    path(
        "<uuid:order_id>/rider-cancel/",
        cancel_order,
        name="rider_cancel_order",
    ),
    path("cancel/<str:order_number>/", CancelOrderView.as_view(), name="cancel_order"),
    # Generic order detail (must come last to avoid matching specific endpoints)
    path("<str:order_number>/", OrderDetailView.as_view(), name="order_detail"),
]
