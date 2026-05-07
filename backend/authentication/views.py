from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta
from .models import User, Address
from .serializers import (
    UserSerializer,
    SignupSerializer,
    LoginSerializer,
    UserProfileSerializer,
    AddressSerializer,
)
from .emails import (
    send_verification_email,
    send_password_reset_email,
    send_mobile_password_reset_email,
)
from .services import OTPService
from .tasks import send_onboarding_email_task
import logging
from django.db import models
from sparky_utils.response import service_response
from sparky_utils.advice import exception_advice
from sparky_utils.exceptions import ServiceException
from devs.models import ErrorLog


logger = logging.getLogger(__name__)


class SignupView(APIView):
    """API endpoint for user registration."""

    permission_classes = [permissions.AllowAny]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        """Register a new merchant user."""
        serializer = SignupSerializer(data=request.data)
        # get the acquisition from the query param

        if serializer.is_valid():
            reg_source = request.query_params.get("source", "web")
            user = serializer.save(registration_source=reg_source)

            # Generate OTP
            otp = OTPService.generate_otp()
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save(update_fields=["otp", "otp_created_at"])

            # Send OTP via SMS and Email
            try:
                OTPService.send_sms_otp(user.phone, otp)
                logger.info(f"OTP SMS sent to {user.phone}")
            except Exception as e:
                logger.error(f"Failed to send OTP SMS: {str(e)}")
                # Continue with signup even if SMS fails

            try:
                OTPService.send_email_otp(user, otp)
                logger.info(f"OTP email sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send OTP email: {str(e)}")
                # Continue with signup even if email fails

            return Response(
                {
                    "success": True,
                    "message": "User created successfully. Please verify your phone and email with the OTP sent.",
                    "user": SignupSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):
    """API endpoint for user login."""

    permission_classes = [permissions.AllowAny]

    @exception_advice(model_object=ErrorLog)
    def post(self, request):
        """Authenticate user and return JWT tokens."""
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "success": True,
                    "message": "Login successful!",
                    "user": UserSerializer(user).data,
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserProfileView(APIView):
    """API endpoint for getting and updating user profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get current user profile."""
        serializer = UserSerializer(request.user)
        return Response(
            {"success": True, "user": serializer.data}, status=status.HTTP_200_OK
        )

    def put(self, request):
        """Update current user profile."""
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Profile updated successfully!",
                    "user": UserSerializer(request.user).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @exception_advice(model_object=ErrorLog)
    def delete(self, request):
        """Soft-deactivate own account by merchant."""
        user = request.user

        # Check for active orders
        active_statuses = [
            "Pending",
            "Assigned",
            "AssignmentAccepted",
            "Started",
            "Pickup",
            "Fulfilling",
            "Arrived",
        ]
        if user.orders.filter(status__in=active_statuses).exists():
            raise ServiceException(
                status_code=400,
                message="Cannot deactivate account with active/ongoing orders.",
            )

        # Soft-deactivate user
        user.is_active = False
        user.save(update_fields=["is_active"])

        # Update merchant profile status
        if hasattr(user, "merchant_profile"):
            profile = user.merchant_profile
            profile.activity_status = "inactive"
            profile.save(update_fields=["activity_status"])

        return service_response(
            status="success",
            message="Your account has been deactivated successfully.",
            data={},
            status_code=200,
        )


class LogoutView(APIView):
    """API endpoint for user logout."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Logout user by blacklisting the refresh token."""
        try:
            refresh_token = request.data.get("refresh_token")

            if not refresh_token:
                return Response(
                    {"success": False, "message": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"success": True, "message": "Logout successful!"},
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Invalid token or token already blacklisted.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class AddressListCreateView(APIView):
    """API endpoint for listing and creating addresses."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all addresses for current user."""
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(
            {"success": True, "addresses": serializer.data}, status=status.HTTP_200_OK
        )

    def post(self, request):
        """Create a new address."""
        serializer = AddressSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Address added successfully!",
                    "address": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class VerifyOTPView(APIView):
    """
    View to verify OTP for phone and email verification.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        email = request.data.get("email")
        otp = request.data.get("otp")

        try:
            if phone:
                user = User.objects.get(phone=phone)
            elif email:
                user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"success": False, "error": "User with this phone number not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Basic OTP validation (e.g., check expiry - say 10 minutes)
        if user.otp != otp:
            return Response(
                {"success": False, "error": "Invalid OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expiry_time = timezone.now() - timedelta(minutes=10)
        if user.otp_created_at < expiry_time:
            return Response(
                {"success": False, "error": "OTP has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark as verified
        user.phone_verified = True
        user.email_verified = True
        user.otp = None  # Clear OTP after verification
        user.save(update_fields=["phone_verified", "email_verified", "otp"])

        # Send onboarding email via Celery
        try:
            send_onboarding_email_task.delay(user.id)
            logger.info(f"Triggered onboarding email task for user {user.email}")
        except Exception as e:
            logger.error(f"Failed to trigger onboarding email task: {str(e)}")

        # Generate tokens for immediate login
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "message": "Verification successful.",
                "user": SignupSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class ResendOTPView(APIView):
    """
    View to resend OTP for verification.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        email = request.data.get("email")

        try:
            if phone:
                user = User.objects.get(phone=phone)
            elif email:
                user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"success": False, "error": "User with this phone number not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Generate new OTP
        otp = OTPService.generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save(update_fields=["otp", "otp_created_at"])

        # Send OTP via SMS and Email
        sms_sent = False
        email_sent = False
        try:
            OTPService.send_sms_otp(user.phone, otp)
            logger.info(f"Resent OTP SMS to {user.phone}")
            sms_sent = True
        except Exception as e:
            logger.error(f"Failed to resend OTP SMS: {str(e)}")

        try:
            OTPService.send_email_otp(user, otp)
            logger.info(f"Resent OTP email to {user.email}")
            email_sent = True
        except Exception as e:
            logger.error(f"Failed to resend OTP email: {str(e)}")

        if not sms_sent and not email_sent:
            return Response(
                {
                    "success": False,
                    "error": "Failed to send OTP. Please try again later.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "success": True,
                "message": "A new OTP has been sent to your phone and email.",
            },
            status=status.HTTP_200_OK,
        )


class AddressDetailView(APIView):
    """API endpoint for updating and deleting a specific address."""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, address_id):
        """Get address object ensuring it belongs to current user."""
        return get_object_or_404(Address, id=address_id, user=request.user)

    def put(self, request, address_id):
        """Update an address."""
        address = self.get_object(request, address_id)
        serializer = AddressSerializer(
            address, data=request.data, partial=True, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Address updated successfully!",
                    "address": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, address_id):
        """Delete an address."""
        address = self.get_object(request, address_id)
        address.delete()

        return Response(
            {"success": True, "message": "Address deleted successfully!"},
            status=status.HTTP_200_OK,
        )


class SetDefaultAddressView(APIView):
    """API endpoint for setting an address as default."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, address_id):
        """Set an address as default."""
        address = get_object_or_404(Address, id=address_id, user=request.user)

        # Unset other defaults
        Address.objects.filter(user=request.user, is_default=True).update(
            is_default=False
        )

        # Set this as default
        address.is_default = True
        address.save()

        return Response(
            {
                "success": True,
                "message": "Default address updated!",
                "address": AddressSerializer(address).data,
            },
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    """API endpoint for verifying email with token."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Verify email using token from query parameter."""
        token = request.query_params.get("token")

        if not token:
            return Response(
                {"success": False, "error": "Verification token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email_verification_token=token)

            # Check if token is expired (7 days)
            if user.email_verification_token_created:
                token_age = timezone.now() - user.email_verification_token_created
                if token_age > timedelta(days=7):
                    return Response(
                        {
                            "success": False,
                            "error": "Verification link has expired. Please request a new one.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Mark email as verified
            user.email_verified = True
            user.email_verification_token = None
            user.email_verification_token_created = None
            user.save(
                update_fields=[
                    "email_verified",
                    "email_verification_token",
                    "email_verification_token_created",
                ]
            )

            logger.info(f"Email verified successfully for user {user.email}")

            return Response(
                {
                    "success": True,
                    "message": "Email verified successfully!",
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"success": False, "error": "Invalid verification token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResendVerificationEmailView(APIView):
    """API endpoint for resending verification email."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Resend verification email to authenticated user."""
        user = request.user

        if user.email_verified:
            return Response(
                {"success": False, "error": "Email is already verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            send_verification_email(user)
            logger.info(f"Verification email resent to {user.email}")

            return Response(
                {
                    "success": True,
                    "message": "Verification email sent successfully! Please check your inbox.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Failed to resend verification email: {str(e)}")
            return Response(
                {
                    "success": False,
                    "error": "Failed to send verification email. Please try again later.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RequestPasswordResetView(APIView):
    """API endpoint for requesting password reset."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Request password reset email."""
        email = request.data.get("email")

        if not email:
            return Response(
                {"success": False, "error": "Email address is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Try to find user with this email
            user = User.objects.filter(email=email).first()

            if user:
                # Send password reset email
                send_password_reset_email(user)
                logger.info(f"Password reset email sent to {email}")

            # Always return success to prevent email enumeration
            return Response(
                {
                    "success": True,
                    "message": "If an account exists with that email, you will receive a password reset link shortly.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in password reset request: {str(e)}")
            # Still return success to prevent email enumeration
            return Response(
                {
                    "success": True,
                    "message": "If an account exists with that email, you will receive a password reset link shortly.",
                },
                status=status.HTTP_200_OK,
            )


class ResetPasswordView(APIView):
    """API endpoint for resetting password with token."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Reset password using token."""
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        # Validate input
        if not token:
            return Response(
                {"success": False, "error": "Reset token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not new_password or not confirm_password:
            return Response(
                {"success": False, "error": "Both password fields are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return Response(
                {"success": False, "error": "Passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 6:
            return Response(
                {
                    "success": False,
                    "error": "Password must be at least 6 characters long",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Find user with this token
            user = User.objects.get(password_reset_token=token)

            # Check if token is expired (15 mins)
            if user.password_reset_token_created:
                token_age = timezone.now() - user.password_reset_token_created
                if token_age > timedelta(minutes=15):
                    return Response(
                        {
                            "success": False,
                            "error": "Password reset link has expired. Please request a new one.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Update password
            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_token_created = None
            user.save(
                update_fields=[
                    "password",
                    "password_reset_token",
                    "password_reset_token_created",
                ]
            )

            logger.info(f"Password reset successfully for user {user.email}")

            return Response(
                {
                    "success": True,
                    "message": "Password reset successfully! You can now login with your new password.",
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"success": False, "error": "Invalid or expired reset token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            return Response(
                {
                    "success": False,
                    "error": "An error occurred while resetting your password. Please try again.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyPasswordResetTokenView(APIView):
    """API endpoint for verifying if a password reset token is valid."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Verify token validity."""
        token = request.data.get("token")

        if not token:
            return Response(
                {"success": False, "error": "Reset token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Find user with this token
            user = User.objects.get(password_reset_token=token)

            # Check if token is expired (15 mins)
            if user.password_reset_token_created:
                token_age = timezone.now() - user.password_reset_token_created
                if token_age > timedelta(minutes=15):
                    return Response(
                        {
                            "success": False,
                            "error": "Password reset link has expired. Please request a new one.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Token is valid
            return Response(
                {
                    "success": True,
                    "message": "Token is valid.",
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"success": False, "error": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MobileRequestPasswordResetView(APIView):
    """API endpoint for requesting an OTP to reset password (Mobile App)."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Generate a 6-digit OTP and send via SMS and Email."""
        email = request.data.get("email")
        phone_number = request.data.get("phone")

        if not email and not phone_number:
            return Response(
                {"success": False, "error": "Email or phone number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Try to find user with this identifier (email or phone)
            if email:
                user = User.objects.get(email=email)
            elif phone_number:
                user = User.objects.get(phone=phone_number)

            if user:
                # Generate a 6-digit OTP
                otp = OTPService.generate_otp()

                # Save token to user
                user.password_reset_token = otp
                user.password_reset_token_created = timezone.now()
                user.save(
                    update_fields=[
                        "password_reset_token",
                        "password_reset_token_created",
                    ]
                )

                # Send OTP via SMS
                try:
                    # using the existing WhisperSMS service implementation
                    OTPService.send_sms_otp(user.phone, otp)
                    logger.info(f"Mobile password reset SMS sent to {user.phone}")
                except Exception as e:
                    logger.error(
                        f"Failed to send mobile reset SMS to {user.phone}: {str(e)}"
                    )

                # Send OTP via Email
                try:
                    send_mobile_password_reset_email(user, otp)
                    logger.info(f"Mobile password reset email sent to {user.email}")
                except Exception as e:
                    logger.error(
                        f"Failed to send mobile reset email to {user.email}: {str(e)}"
                    )

            # Always return success to prevent user enumeration
            return Response(
                {
                    "success": True,
                    "message": "If an account exists with that information, a 6-digit reset code has been sent via SMS and Email.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in mobile password reset request: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "An error occurred while processing your request. Please try again.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MobileResetPasswordView(APIView):
    """API endpoint for verifying OTP and resetting password (Mobile App)."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Validate the 6-digit OTP and update the user's password."""
        identifier = request.data.get("email") or request.data.get("phone")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        # Validate input
        if not identifier or not otp:
            return Response(
                {"success": False, "error": "Email/Phone and OTP are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not new_password or not confirm_password:
            return Response(
                {"success": False, "error": "Both password fields are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return Response(
                {"success": False, "error": "Passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 6:
            return Response(
                {
                    "success": False,
                    "error": "Password must be at least 6 characters long.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Find user with this identifier (email or phone)
            user = User.objects.filter(
                models.Q(email=identifier) | models.Q(phone=identifier)
            ).first()

            if not user or user.password_reset_token != otp:
                return Response(
                    {"success": False, "error": "Invalid or expired reset code."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if OTP is expired (15 minutes limit for mobile OTP)
            if user.password_reset_token_created:
                token_age = timezone.now() - user.password_reset_token_created
                if token_age > timedelta(minutes=15):
                    return Response(
                        {
                            "success": False,
                            "error": "Your reset code has expired. Please request a new one.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Update password
            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_token_created = None
            user.save(
                update_fields=[
                    "password",
                    "password_reset_token",
                    "password_reset_token_created",
                ]
            )

            logger.info(f"Mobile password reset successfully for user {user.phone}")

            return Response(
                {
                    "success": True,
                    "message": "Password reset successfully! You can now login with your new password.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error executing mobile password reset: {str(e)}")
            return Response(
                {
                    "success": False,
                    "error": "An error occurred while resetting your password. Please try again.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------------------
# Merchant Notifications
# ---------------------------------------------------------------------------

from dispatcher.permissions import IsMerchant  # noqa: E402
from dispatcher.models import (
    MerchantDevice,
    MerchantNotification,
    MerchantNotificationSettings,
)  # noqa: E402
from .serializers import (  # noqa: E402
    MerchantDeviceSerializer,
    MerchantNotificationSerializer,
    MerchantNotificationSettingsSerializer,
)


class MerchantDeviceRegistrationView(APIView):
    """
    POST /api/auth/device/
    Register or update a merchant's mobile device for push notifications.
    Uses device_id as the unique key — safe to call on every app launch.
    """

    permission_classes = [permissions.IsAuthenticated, IsMerchant]

    def post(self, request):
        serializer = MerchantDeviceSerializer(data=request.data)
        if not serializer.is_valid():
            return service_response(
                status="error",
                message="Invalid device data.",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        merchant = request.user.merchant_profile
        data = serializer.validated_data

        MerchantDevice.objects.update_or_create(
            device_id=data["device_id"],
            defaults={
                "merchant": merchant,
                "fcm_token": data["fcm_token"],
                "platform": data["platform"],
                "model_name": data["model_name"],
                "os_version": data["os_version"],
                "app_version": data["app_version"],
                "is_active": True,
            },
        )

        return service_response(
            status="success",
            message="Device registered successfully.",
            status_code=status.HTTP_200_OK,
        )


class MerchantNotificationListView(APIView):
    """
    GET /api/auth/notifications/
    Returns all notifications for the authenticated merchant, newest first.
    """

    permission_classes = [permissions.IsAuthenticated, IsMerchant]

    def get(self, request):
        merchant = request.user.merchant_profile
        notifications = MerchantNotification.objects.filter(merchant=merchant)
        serializer = MerchantNotificationSerializer(notifications, many=True)
        return service_response(
            status="success",
            message="Notifications fetched successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class MerchantNotificationDetailView(APIView):
    """
    GET /api/auth/notifications/<uuid:pk>/
    Returns a single notification belonging to the authenticated merchant.
    """

    permission_classes = [permissions.IsAuthenticated, IsMerchant]

    def get(self, request, pk):
        merchant = request.user.merchant_profile
        notification = get_object_or_404(MerchantNotification, pk=pk, merchant=merchant)
        serializer = MerchantNotificationSerializer(notification)
        return service_response(
            status="success",
            message="Notification fetched successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class MerchantNotificationMarkReadView(APIView):
    """
    POST /api/auth/notifications/<uuid:pk>/read/
    Marks a single notification as read.
    """

    permission_classes = [permissions.IsAuthenticated, IsMerchant]

    def post(self, request, pk):
        merchant = request.user.merchant_profile
        notification = get_object_or_404(MerchantNotification, pk=pk, merchant=merchant)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return service_response(
            status="success",
            message="Notification marked as read.",
            status_code=status.HTTP_200_OK,
        )


class MerchantNotificationMarkAllReadView(APIView):
    """
    POST /api/auth/notifications/read-all/
    Marks all unread notifications as read for the authenticated merchant.
    """

    permission_classes = [permissions.IsAuthenticated, IsMerchant]

    def post(self, request):
        merchant = request.user.merchant_profile
        updated = MerchantNotification.objects.filter(
            merchant=merchant, is_read=False
        ).update(is_read=True)
        return service_response(
            status="success",
            message=f"{updated} notification(s) marked as read.",
            status_code=status.HTTP_200_OK,
        )


class MerchantNotificationSettingsView(APIView):
    """
    GET  /api/auth/notifications/settings/  — retrieve current toggle preferences.
    PATCH /api/auth/notifications/settings/ — update one or more toggles.
    """

    permission_classes = [permissions.IsAuthenticated, IsMerchant]

    def _get_settings(self, merchant):
        obj, _ = MerchantNotificationSettings.objects.get_or_create(merchant=merchant)
        return obj

    def get(self, request):
        settings_obj = self._get_settings(request.user.merchant_profile)
        serializer = MerchantNotificationSettingsSerializer(settings_obj)
        return service_response(
            status="success",
            message="Notification settings fetched successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    def patch(self, request):
        settings_obj = self._get_settings(request.user.merchant_profile)
        serializer = MerchantNotificationSettingsSerializer(
            settings_obj, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return service_response(
                status="error",
                message="Invalid settings data.",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return service_response(
            status="success",
            message="Notification settings updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class MerchantNotificationDeleteView(APIView):
    """
    DELETE /api/auth/notifications/<uuid:pk>/
    Deletes a single notification belonging to the authenticated merchant.
    """

    permission_classes = [permissions.IsAuthenticated, IsMerchant]

    @exception_advice(model_object=ErrorLog)
    def delete(self, request, pk):
        merchant = request.user.merchant_profile
        notification = get_object_or_404(MerchantNotification, pk=pk, merchant=merchant)
        notification.delete()
        return service_response(
            status="success",
            message="Notification deleted successfully.",
            status_code=status.HTTP_200_OK,
        )


class MerchantNotificationDeleteAllView(APIView):
    """
    DELETE /api/auth/notifications/delete-all/
    Deletes all notifications for the authenticated merchant.
    """

    permission_classes = [permissions.IsAuthenticated, IsMerchant]

    @exception_advice(model_object=ErrorLog)
    def delete(self, request):
        merchant = request.user.merchant_profile
        count, _ = MerchantNotification.objects.filter(merchant=merchant).delete()
        return service_response(
            status="success",
            message=f"{count} notification(s) deleted successfully.",
            status_code=status.HTTP_200_OK,
        )
