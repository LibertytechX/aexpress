from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RiderViewSet, OrderViewSet, MerchantViewSet

router = DefaultRouter()
router.register(r"riders", RiderViewSet)
router.register(r"orders", OrderViewSet)
router.register(r"merchants", MerchantViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
