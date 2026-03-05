from rest_framework import serializers
from .models import Webhook


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = [
            "id",
            "event_name",
            "url",
            "secret_key",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_event_name(self, value):
        """Ensure event_name is lowercase and valid."""
        return value.lower()
