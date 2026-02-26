from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RiderViewSet,
    OrderViewSet,
    MerchantViewSet,
    SystemSettingsView,
    RiderOnboardingView,
    S3PresignedUrlView,
    ActivityFeedView,
    AblyTokenView,
    ZoneViewSet,
    RelayNodeViewSet,
)

router = DefaultRouter()
router.register(r"riders", RiderViewSet)
router.register(r"orders", OrderViewSet)
router.register(r"merchants", MerchantViewSet)
router.register(r"zones", ZoneViewSet)
router.register(r"relay-nodes", RelayNodeViewSet)

urlpatterns = [
    path("settings/", SystemSettingsView.as_view(), name="system-settings"),
    path("riders/onboarding/", RiderOnboardingView.as_view(), name="rider-onboarding"),
    path("s3/presigned-url/", S3PresignedUrlView.as_view(), name="s3-presigned-url"),
    path("activity/", ActivityFeedView.as_view(), name="activity-feed"),
    path("ably-token/", AblyTokenView.as_view(), name="ably-token"),
    path("", include(router.urls)),
]
