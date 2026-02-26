from django.urls import path
from .views import (
    RiderLoginView,
    RiderTokenRefreshView,
    RiderDeviceRegistrationView,
    RiderUpdatePermissionsView,
    RiderMeView,
    RiderToggleDutyView,
    AreaDemandListView,
    RiderOrderHistoryView,
    RiderOrderDetailView,
    OrderOfferListView,
    OrderOfferAcceptView,
    RiderEarningsView,
    RiderTodayTripsView,
    RiderWalletInfoView,
    RiderTransactionListView,
    RiderLocationUpdateView,
)

app_name = "riders"

urlpatterns = [
    path("auth/login/", RiderLoginView.as_view(), name="rider-login"),
    path("auth/refresh/", RiderTokenRefreshView.as_view(), name="rider-token-refresh"),
    path(
        "device/", RiderDeviceRegistrationView.as_view(), name="rider-device-register"
    ),
    path(
        "device/permissions/",
        RiderUpdatePermissionsView.as_view(),
        name="rider-device-permissions",
    ),
    path("auth/me/", RiderMeView.as_view(), name="rider-me"),
    path("duty/", RiderToggleDutyView.as_view(), name="rider-duty-toggle"),
    path("area-demand/", AreaDemandListView.as_view(), name="area-demand-list"),
    path(
        "orders/history/", RiderOrderHistoryView.as_view(), name="rider-order-history"
    ),
    path("orders/offers/", OrderOfferListView.as_view(), name="rider-order-offers"),
    path(
        "orders/offers/<uuid:offer_id>/accept/",
        OrderOfferAcceptView.as_view(),
        name="rider-offer-accept",
    ),
    path(
        "orders/<str:order_id>/",
        RiderOrderDetailView.as_view(),
        name="rider-order-detail",
    ),
    path("earnings/", RiderEarningsView.as_view(), name="rider-earnings"),
    path("wallet/info/", RiderWalletInfoView.as_view(), name="rider-wallet-info"),
    path(
        "wallet/transactions/",
        RiderTransactionListView.as_view(),
        name="rider-wallet-transactions",
    ),
    path("orders-today/", RiderTodayTripsView.as_view(), name="rider-orders-today"),
    path(
        "location/update/",
        RiderLocationUpdateView.as_view(),
        name="rider-location-update",
    ),
]
