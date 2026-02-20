from django.urls import path
from .views import RiderLoginView

urlpatterns = [
    path("auth/login/", RiderLoginView.as_view(), name="rider-login"),
]
