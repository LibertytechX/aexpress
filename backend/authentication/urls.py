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
    VerifyPasswordResetTokenView,
    ResetPasswordView,
    VerifyOTPView,
    ResendOTPView,
    MobileRequestPasswordResetView,
    MobileResetPasswordView,
    MerchantDeviceRegistrationView,
    MerchantNotificationListView,
    MerchantNotificationDetailView,
    MerchantNotificationMarkReadView,
    MerchantNotificationMarkAllReadView,
    MerchantNotificationSettingsView,
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
    path(
        "verify-password-reset-token/",
        VerifyPasswordResetTokenView.as_view(),
        name="verify_password_reset_token",
    ),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    path(
        "mobile/request-password-reset/",
        MobileRequestPasswordResetView.as_view(),
        name="mobile_request_password_reset",
    ),
    path(
        "mobile/reset-password/",
        MobileResetPasswordView.as_view(),
        name="mobile_reset_password",
    ),
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
    # Merchant device & notification endpoints
    path(
        "device/",
        MerchantDeviceRegistrationView.as_view(),
        name="merchant_device_register",
    ),
    path(
        "notifications/",
        MerchantNotificationListView.as_view(),
        name="merchant_notification_list",
    ),
    path(
        "notifications/read-all/",
        MerchantNotificationMarkAllReadView.as_view(),
        name="merchant_notification_read_all",
    ),
    path(
        "notifications/settings/",
        MerchantNotificationSettingsView.as_view(),
        name="merchant_notification_settings",
    ),
    path(
        "notifications/<uuid:pk>/",
        MerchantNotificationDetailView.as_view(),
        name="merchant_notification_detail",
    ),
    path(
        "notifications/<uuid:pk>/read/",
        MerchantNotificationMarkReadView.as_view(),
        name="merchant_notification_mark_read",
    ),
]
