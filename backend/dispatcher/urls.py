from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RiderViewSet, VehicleViewSet

router = DefaultRouter()
router.register(r"riders", RiderViewSet)
router.register(r"vehicles", VehicleViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
