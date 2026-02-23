from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SignupView,
    LoginView,
    UserProfileView,
    LogoutView,
    AddressListCreateView,
    AddressDetailView,
    SetDefaultAddressView,
    VerifyEmailView,
    ResendVerificationEmailView,
    RequestPasswordResetView,
    ResetPasswordView,
    VerifyOTPView,
    ResendOTPView,
)

app_name = "authentication"

urlpatterns = [
    # Authentication endpoints
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Email verification endpoints
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend_otp"),
    path(
        "resend-verification/",
        ResendVerificationEmailView.as_view(),
        name="resend_verification",
    ),
    # Password reset endpoints
    path(
        "request-password-reset/",
        RequestPasswordResetView.as_view(),
        name="request_password_reset",
    ),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    # User profile endpoints
    path("me/", UserProfileView.as_view(), name="user_profile"),
    path("profile/", UserProfileView.as_view(), name="update_profile"),
    # Address endpoints
    path("addresses/", AddressListCreateView.as_view(), name="address_list_create"),
    path(
        "addresses/<uuid:address_id>/",
        AddressDetailView.as_view(),
        name="address_detail",
    ),
    path(
        "addresses/<uuid:address_id>/set-default/",
        SetDefaultAddressView.as_view(),
        name="set_default_address",
    ),
]
