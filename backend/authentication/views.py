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
from .emails import send_verification_email, send_password_reset_email
from .services import OTPService
import logging

logger = logging.getLogger(__name__)


class SignupView(APIView):
    """API endpoint for user registration."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Register a new merchant user."""
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

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

        except Exception as e:
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
        otp = request.data.get("otp")

        if not phone or not otp:
            return Response(
                {"success": False, "error": "Phone and OTP are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(phone=phone)
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

        if not phone:
            return Response(
                {"success": False, "error": "Phone number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(phone=phone)
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

            # Check if token is expired (1 hour)
            if user.password_reset_token_created:
                token_age = timezone.now() - user.password_reset_token_created
                if token_age > timedelta(hours=1):
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
