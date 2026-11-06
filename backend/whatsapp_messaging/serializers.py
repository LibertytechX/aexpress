from rest_framework import serializers


class SendTestWhatsAppSerializer(serializers.Serializer):
    """
    Serializer for testing WhatsApp message sending.
    """
    phone_number = serializers.CharField(
        max_length=20,
        help_text="Phone number in international format (e.g., 2348012345678)"
    )
    message_text = serializers.CharField(
        help_text="Message text to send"
    )
    media_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="Optional URL to image/document"
    )

    def validate_phone_number(self, value):
        """Ensure phone number is in valid format."""
        if not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits."
            )
        if len(value) < 10:
            raise serializers.ValidationError(
                "Phone number must be at least 10 digits."
            )
        return value
