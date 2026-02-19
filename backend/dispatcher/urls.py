from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RiderViewSet, OrderViewSet, MerchantViewSet, SystemSettingsView

router = DefaultRouter()
router.register(r"riders", RiderViewSet)
router.register(r"orders", OrderViewSet)
router.register(r"merchants", MerchantViewSet)

urlpatterns = [
    path("settings/", SystemSettingsView.as_view(), name="system-settings"),
    path("", include(router.urls)),
]
