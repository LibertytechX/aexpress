from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RiderViewSet,
    OrderViewSet,
    MerchantViewSet,
    SystemSettingsView,
    RiderOnboardingView,
    S3PresignedUrlView,
)

router = DefaultRouter()
router.register(r"riders", RiderViewSet)
router.register(r"orders", OrderViewSet)
router.register(r"merchants", MerchantViewSet)

urlpatterns = [
    path("settings/", SystemSettingsView.as_view(), name="system-settings"),
    path("riders/onboarding/", RiderOnboardingView.as_view(), name="rider-onboarding"),
    path("s3/presigned-url/", S3PresignedUrlView.as_view(), name="s3-presigned-url"),
    path("", include(router.urls)),
]
