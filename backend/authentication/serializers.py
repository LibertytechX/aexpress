from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


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

