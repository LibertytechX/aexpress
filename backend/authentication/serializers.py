from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Address


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model - used for displaying user data."""

    class Meta:
        model = User
        fields = [
            'id', 'business_name', 'contact_name', 'phone', 'email',
            'address', 'is_active', 'email_verified', 'phone_verified',
            'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login']


class SignupSerializer(serializers.ModelSerializer):
    """Serializer for user registration (3-step signup from frontend)."""

    password = serializers.CharField(write_only=True, min_length=6, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = [
            'business_name', 'contact_name', 'phone', 'email',
            'address', 'password', 'confirm_password'
        ]

    def validate_phone(self, value):
        """Validate phone number format and uniqueness."""
        # Remove spaces and dashes
        phone = value.replace(' ', '').replace('-', '')

        # Check if phone already exists
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("This phone number is already registered.")

        return phone

    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("This email is already registered.")

        return value.lower()

    def validate(self, data):
        """Validate that passwords match."""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        return data

    def create(self, validated_data):
        """Create a new user with hashed password."""
        # Remove confirm_password from validated data
        validated_data.pop('confirm_password', None)

        # Create user using the custom manager (which hashes the password)
        user = User.objects.create_user(
            phone=validated_data['phone'],
            email=validated_data['email'],
            password=validated_data['password'],
            business_name=validated_data['business_name'],
            contact_name=validated_data['contact_name'],
            address=validated_data.get('address', '')
        )

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login with phone and password."""

    phone = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        """Validate credentials and authenticate user."""
        phone = data.get('phone', '').replace(' ', '').replace('-', '')
        password = data.get('password')

        if not phone or not password:
            raise serializers.ValidationError("Phone and password are required.")

        # Try to get the user
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid phone number or password.")

        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

        # Authenticate user
        user = authenticate(username=phone, password=password)

        if not user:
            raise serializers.ValidationError("Invalid phone number or password.")

        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ['business_name', 'contact_name', 'email', 'address']

    def validate_email(self, value):
        """Validate email uniqueness (excluding current user)."""
        user = self.instance
        if User.objects.filter(email=value.lower()).exclude(id=user.id).exists():
            raise serializers.ValidationError("This email is already in use.")

        return value.lower()


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address model."""

    class Meta:
        model = Address
        fields = ['id', 'label', 'address', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate address data."""
        user = self.context['request'].user

        # Check max 3 addresses per user (only for new addresses)
        if not self.instance:
            existing_count = Address.objects.filter(user=user).count()
            if existing_count >= 3:
                raise serializers.ValidationError("Maximum of 3 addresses allowed.")

        # Check unique label per user
        label = data.get('label')
        if label:
            query = Address.objects.filter(user=user, label=label)
            if self.instance:
                query = query.exclude(id=self.instance.id)
            if query.exists():
                raise serializers.ValidationError({"label": "You already have an address with this label."})

        return data

    def create(self, validated_data):
        """Create address with user from context."""
        user = self.context['request'].user
        return Address.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        """Update address and handle default flag."""
        is_default = validated_data.get('is_default', instance.is_default)

        # If setting as default, unset other defaults
        if is_default and not instance.is_default:
            Address.objects.filter(user=instance.user, is_default=True).update(is_default=False)

        return super().update(instance, validated_data)

