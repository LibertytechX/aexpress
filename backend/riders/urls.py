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
        "orders/<str:order_id>/",
        RiderOrderDetailView.as_view(),
        name="rider-order-detail",
    ),
]
