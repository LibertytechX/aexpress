from django.urls import path
from .views import (
    VehicleListView,
    QuickSendView,
    MultiDropView,
    BulkImportView,
    MergeGroupedOrdersView,
    OrderListView,
    OrderDetailView,
    OrderStatsView,
    CancelOrderView,
    CancelableOrdersView,
    CalculateFareView,
    BulkCalculateFareView,
    VehicleUpdateView,
    AssignedOrdersView,
    AssignedOrderDetailView,
    AssignedRoutesView,
    OrderPickupView,
    cancel_order,
    DeliveryStartView,
    DeliveryCompleteView,
    OrderStartView,
    OrderArrivedView,
    OrderCompleteView,
    OrderStatusChangeView,
    OrderPayNowView,
    OrderEventAPIView,
    SmartParcelStatesView,
    SmartParcelCitiesByStateView,
    SmartParcelBoxesByCityView,
    SmartParcelAssignedBoxesByCityView,
    SmartParcelBoxDetailView,
    SmartParcelAvailableBoxesView,
    SmartParcelLockerSizesView,
    SmartParcelCreateParcelView,
    SmartParcelParcelDetailView,
    SmartParcelCancelParcelView,
    SmartParcelPendingPickupsView,
    SmartParcelResolveCollectCodeView,
    SmartParcelSimulateDropView,
    SmartParcelSimulateCollectView,
)
from .escrow_views import (
    ReleaseEscrowView,
    RefundEscrowView,
    EscrowStatusView,
    EscrowHistoryView,
)
from .places_views import (
    PlacesAutocompleteView,
    PlaceDetailsView,
    ReverseGeocodeView,
    GeocodeView,
)

app_name = "orders"

urlpatterns = [
    # Places fallback endpoints
    path("places/autocomplete/", PlacesAutocompleteView.as_view(), name="places_autocomplete"),
    path("places/details/", PlaceDetailsView.as_view(), name="places_details"),
    path("places/reverse-geocode/", ReverseGeocodeView.as_view(), name="places_reverse_geocode"),
    path("places/geocode/", GeocodeView.as_view(), name="places_geocode"),
    # Vehicle endpoints
    path("vehicles/", VehicleListView.as_view(), name="vehicle_list"),
    path("vehicles/<int:id>/", VehicleUpdateView.as_view(), name="vehicle_update"),
    # Order creation endpoints
    path("quick-send/", QuickSendView.as_view(), name="quick_send"),
    path("multi-drop/", MultiDropView.as_view(), name="multi_drop"),
    path("bulk-import/", BulkImportView.as_view(), name="bulk_import"),
    path(
        "merge-grouped-orders/",
        MergeGroupedOrdersView.as_view(),
        name="merge_grouped_orders",
    ),
    path("calculate-fare/", CalculateFareView.as_view(), name="calculate_fare"),
    path(
        "bulk-calculate-fare/",
        BulkCalculateFareView.as_view(),
        name="bulk_calculate_fare",
    ),
    # Order management endpoints
    path("", OrderListView.as_view(), name="order_list"),
    path("assigned/", AssignedOrdersView.as_view(), name="assigned_orders"),
    path(
        "assigned/<str:order_number>/",
        AssignedOrderDetailView.as_view(),
        name="assigned_order_detail",
    ),
    path("<str:order_number>/events/", OrderEventAPIView.as_view(), name="order_events"),
    path("assigned-routes/", AssignedRoutesView.as_view(), name="assigned_routes"),
    path("pickup/", OrderPickupView.as_view(), name="order_pickup"),
    path("start/", OrderStartView.as_view(), name="order_start"),
    path("arrived/", OrderArrivedView.as_view(), name="order_arrived"),
    path("status/", OrderStatusChangeView.as_view(), name="order_status_change"),
    # path("<str:order_number>/complete/", OrderCompleteView.as_view(), name="order_complete"),
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
    path("<str:order_number>/pay-now/", OrderPayNowView.as_view(), name="order_pay_now"),
    # Generic order detail (must come last to avoid matching specific endpoints)
    path("<str:order_number>/", OrderDetailView.as_view(), name="order_detail"),

    # ------------------------------------------------------------------
    # SmartParcel Locker Delivery Integration
    # ------------------------------------------------------------------
    # Geography
    path("smart-parcel/states/", SmartParcelStatesView.as_view(), name="sp_states"),
    path(
        "smart-parcel/states/<str:state_id>/cities/",
        SmartParcelCitiesByStateView.as_view(),
        name="sp_cities_by_state",
    ),
    # Boxes
    path(
        "smart-parcel/boxes/city/<str:city_id>/",
        SmartParcelBoxesByCityView.as_view(),
        name="sp_boxes_by_city",
    ),
    path(
        "smart-parcel/boxes/assigned/city/<str:city_id>/",
        SmartParcelAssignedBoxesByCityView.as_view(),
        name="sp_assigned_boxes_by_city",
    ),
    path(
        "smart-parcel/boxes/available/",
        SmartParcelAvailableBoxesView.as_view(),
        name="sp_available_boxes",
    ),
    path(
        "smart-parcel/boxes/<str:box_id>/",
        SmartParcelBoxDetailView.as_view(),
        name="sp_box_detail",
    ),
    # Locker sizes
    path(
        "smart-parcel/locker-sizes/",
        SmartParcelLockerSizesView.as_view(),
        name="sp_locker_sizes",
    ),
    # Parcels
    path(
        "smart-parcel/parcels/",
        SmartParcelCreateParcelView.as_view(),
        name="sp_create_parcel",
    ),
    path(
        "smart-parcel/parcels/pending-pickups/",
        SmartParcelPendingPickupsView.as_view(),
        name="sp_pending_pickups",
    ),
    path(
        "smart-parcel/parcels/resolve-collect-code/<str:collect_code>/",
        SmartParcelResolveCollectCodeView.as_view(),
        name="sp_resolve_collect_code",
    ),
    path(
        "smart-parcel/parcels/<str:tracking_number>/",
        SmartParcelParcelDetailView.as_view(),
        name="sp_parcel_detail",
    ),
    path(
        "smart-parcel/parcels/<str:tracking_number>/cancel/",
        SmartParcelCancelParcelView.as_view(),
        name="sp_cancel_parcel",
    ),
    # Simulation (sandbox only)
    path(
        "smart-parcel/locker/simulate/drop/",
        SmartParcelSimulateDropView.as_view(),
        name="sp_simulate_drop",
    ),
    path(
        "smart-parcel/locker/simulate/collect/",
        SmartParcelSimulateCollectView.as_view(),
        name="sp_simulate_collect",
    ),
]
