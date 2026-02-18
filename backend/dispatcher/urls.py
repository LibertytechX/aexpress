from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RiderViewSet, OrderViewSet

router = DefaultRouter()
router.register(r"riders", RiderViewSet)
router.register(r"orders", OrderViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
