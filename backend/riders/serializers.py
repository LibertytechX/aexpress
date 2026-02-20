from rest_framework import serializers
from django.contrib.auth import authenticate
from dispatcher.models import Rider
from authentication.models import User
from .models import RiderAuth


class RiderMeSerializer(serializers.ModelSerializer):
    """
    Basic rider profile data for mobile app.
    Pulling contact info from the linked User model.
    """

    firstName = serializers.CharField(source="user.first_name", read_only=True)
    lastName = serializers.CharField(source="user.last_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Rider
        fields = [
            "id",
            "rider_id",
            "status",
            "firstName",
            "lastName",
            "phone",
            "email",
            "vehicle_model",
            "vehicle_plate_number",
            "rating",
            "total_deliveries",
        ]


class RiderLoginSerializer(serializers.Serializer):
    """
    Serializer for rider login.
    Leverages Django authenticate() and includes device tracking fields.
    """

    phone = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    device_id = serializers.CharField(max_length=255, required=False, default="")
    device_name = serializers.CharField(max_length=255, required=False, default="")
    device_os = serializers.CharField(max_length=50, required=False, default="android")
    fcm_token = serializers.CharField(max_length=500, required=False, default="")

    def validate(self, data):
        phone = data.get("phone", "").replace(" ", "").replace("-", "")
        password = data.get("password")

        if not phone or not password:
            raise serializers.ValidationError("Phone and password are required.")

        # Try to get the user
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid phone number or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

        # Authenticate user
        user = authenticate(username=phone, password=password)
        if not user:
            raise serializers.ValidationError("Invalid phone number or password.")

        # Ensure user has a rider profile
        try:
            rider = user.rider_profile
        except Rider.DoesNotExist:
            raise serializers.ValidationError(
                "No rider profile associated with this account."
            )

        data["user"] = user
        data["rider"] = rider
        return data
