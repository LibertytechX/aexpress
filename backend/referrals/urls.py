from django.urls import path
from .views import (
    ReferralOverviewView,
    ReferralBusinessListView,
    RegisterReferralBusinessView,
)

app_name = "referrals"

urlpatterns = [
    path("overview/", ReferralOverviewView.as_view(), name="referral-overview"),
    path("businesses/", ReferralBusinessListView.as_view(), name="referral-businesses"),
    path(
        "register-business/",
        RegisterReferralBusinessView.as_view(),
        name="referral-register-business",
    ),
]
