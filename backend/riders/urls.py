from django.urls import path
from .views import RiderLoginView, RiderTokenRefreshView

urlpatterns = [
    path("auth/login/", RiderLoginView.as_view(), name="rider-login"),
    path("auth/refresh/", RiderTokenRefreshView.as_view(), name="rider-token-refresh"),
]
