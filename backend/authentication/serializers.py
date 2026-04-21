from rest_framework import serializers
from django.contrib.auth import authenticate
from sparky_utils.exceptions import ServiceException
from .models import User, Address


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model - used for displaying user data."""

    class Meta:
        model = User
        fields = [
            "id",
            "business_name",
            "contact_name",
            "phone",
            "email",
            "address",
            "is_active",
            "email_verified",
            "phone_verified",
            "created_at",
            "updated_at",
            "last_login",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "last_login"]


class SignupSerializer(serializers.ModelSerializer):
    """Serializer for user registration (3-step signup from frontend)."""

    password = serializers.CharField(
        write_only=True, min_length=6, style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "business_name",
            "contact_name",
            "phone",
            "email",
            "address",
            "password",
            "confirm_password",
            "usertype",
            "registration_source",
            "referral_code",
        ]
        extra_kwargs = {
            "usertype": {
                "required": False
            }  # Optional, defaults to Merchant if not provided, or handle in create
        }

    def validate_phone(self, value):
        """Validate phone number format and uniqueness."""
        # Remove spaces and dashes
        phone = value.replace(" ", "").replace("-", "")

        # Check if phone already exists
        if User.objects.filter(phone=phone).exists():
            raise ServiceException(
                status_code=400, message="This phone number is already registered."
            )

        return phone

    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value.lower()).exists():
            raise ServiceException(
                status_code=400, message="This email is already registered."
            )

        return value.lower()

    def validate(self, data):
        """Validate that passwords match."""
        if data.get("password") != data.get("confirm_password"):
            raise ServiceException(status_code=400, message="Passwords do not match.")

        return data

    def create(self, validated_data):
        """Create a new user with hashed password."""
        # Remove confirm_password from validated data
        validated_data.pop("confirm_password", None)

        # Get usertype or default to Merchant (or whatever default behavior is desired)
        # If usertype is passed, it will be in validated_data

        # Create user using the custom manager (which hashes the password)
        user = User.objects.create_user(
            phone=validated_data["phone"],
            email=validated_data["email"],
            password=validated_data["password"],
            business_name=validated_data.get("business_name", ""),
            contact_name=validated_data.get("contact_name", ""),
            address=validated_data.get("address", ""),
            usertype=validated_data.get("usertype", "Merchant"),
            registration_source=validated_data.get("registration_source"),
            referral_code=validated_data.get("referral_code"),
        )

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login with phone and password."""

    phone = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate(self, data):
        """Validate credentials and authenticate user."""
        phone = data.get("phone", "").replace(" ", "").replace("-", "")
        password = data.get("password")

        if not phone or not password:
            raise ServiceException(
                status_code=400, message="Phone and password are required."
            )

        # Try to get the user
        # should try phone number combos
        phone_2, phone_3 = "", ""
        phone_numbers = [phone]
        if phone.startswith("0"):
            phone_2 = "+234" + phone[1:]
            phone_3 = phone[1:]
            phone_numbers.append(phone_2)
            phone_numbers.append(phone_3)
        elif len(phone) == 10:
            phone_3 = "0" + phone
            phone_2 = "+234" + phone
            phone_numbers.append(phone_2)
            phone_numbers.append(phone_3)
        elif phone.startswith("+234"):
            phone_2 = phone[4:]
            phone_3 = "0" + phone_2
            phone_numbers.append(phone_2)
            phone_numbers.append(phone_3)
        print("Let's see the phone numbers: ", phone_numbers)
        user = User.objects.filter(phone__in=phone_numbers)
        if user.count() == 0:
            raise ServiceException(
                status_code=400, message="Invalid phone number or password."
            )

        user = None
        # try authentication for phone with the given password
        for phone_number in phone_numbers:
            user = authenticate(username=phone_number, password=password)
            if user:
                if not user.is_active:
                    raise ServiceException(
                        status_code=400, message="This account has been deactivated."
                    )
                break
        if not user:
            raise ServiceException(
                status_code=400, message="Invalid phone number or password."
            )

        data["user"] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ["business_name", "contact_name", "email", "address"]

    def validate_email(self, value):
        """Validate email uniqueness (excluding current user)."""
        user = self.instance
        if User.objects.filter(email=value.lower()).exclude(id=user.id).exists():
            raise ServiceException(
                status_code=400, message="This email is already in use."
            )

        return value.lower()


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address model."""

    class Meta:
        model = Address
        fields = ["id", "label", "address", "is_default", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validate address data."""
        user = self.context["request"].user

        # Check max 3 addresses per user (only for new addresses)
        if not self.instance:
            existing_count = Address.objects.filter(user=user).count()
            if existing_count >= 3:
                raise ServiceException(
                    status_code=400, message="Maximum of 3 addresses allowed."
                )

        # Check unique label per user
        label = data.get("label")
        if label:
            query = Address.objects.filter(user=user, label=label)
            if self.instance:
                query = query.exclude(id=self.instance.id)
            if query.exists():
                raise ServiceException(
                    status_code=400,
                    message="You already have an address with this label.",
                )

        return data

    def create(self, validated_data):
        """Create address with user from context."""
        user = self.context["request"].user
        return Address.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        """Update address and handle default flag."""
        is_default = validated_data.get("is_default", instance.is_default)

        # If setting as default, unset other defaults
        if is_default and not instance.is_default:
            Address.objects.filter(user=instance.user, is_default=True).update(
                is_default=False
            )

        return super().update(instance, validated_data)


# ---------------------------------------------------------------------------
# Merchant Notifications
# ---------------------------------------------------------------------------

from dispatcher.models import (
    MerchantNotification,
    MerchantNotificationSettings,
)  # noqa: E402


class MerchantDeviceSerializer(serializers.Serializer):
    """Validates device registration input for merchant mobile apps."""

    device_id = serializers.CharField(max_length=255)
    fcm_token = serializers.CharField(
        max_length=500, required=False, allow_blank=True, default=""
    )
    platform = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=""
    )
    model_name = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )
    os_version = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=""
    )
    app_version = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=""
    )


class MerchantNotificationSerializer(serializers.ModelSerializer):
    """Read-only serializer for merchant notification list and detail responses."""

    class Meta:
        model = MerchantNotification
        fields = ["id", "title", "body", "data", "is_read", "created_at"]
        read_only_fields = fields


class MerchantNotificationSettingsSerializer(serializers.ModelSerializer):
    """Read/write serializer for per-merchant notification preference toggles."""

    class Meta:
        model = MerchantNotificationSettings
        fields = [
            "push_enabled",
            "order_assigned",
            "order_completed",
            "order_cancelled",
            "wallet_credit",
            "marketing",
        ]
