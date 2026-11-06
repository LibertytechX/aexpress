from typing import Any, Dict, List, Optional
from rest_framework import serializers
from sparky_utils.exceptions import ServiceException
from .models import Webhook
from .enums import WebhookEventEnum


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = [
            "id",
            "event_name",
            "merchant",
            "url",
            "secret_key",
            "is_active",
            "events",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validates that either event_name or events is provided.

        Args:
            attrs (Dict[str, Any]): Dictionary of serializer input attributes.

        Returns:
            Dict[str, Any]: Validated attributes dictionary.

        Raises:
            ServiceException: If neither event_name nor events is provided.
        """
        event_name: Optional[str] = attrs.get("event_name")
        events: Optional[List[str]] = attrs.get("events")

        # Account for partial updates (PATCH) where instance already exists
        if self.instance:
            if "event_name" not in attrs:
                event_name = self.instance.event_name
            if "events" not in attrs:
                events = self.instance.events

        if not event_name and not events:
            raise ServiceException(
                status_code=400,
                message="Either event_name or events must be provided",
            )

        return attrs

    def validate_event_name(self, value: str) -> str:
        """Ensure event_name is lowercase and valid.

        Args:
            value (str): Event name string.

        Returns:
            str: Lowercased event name.
        """
        return value.lower()

    def validate_events(self, value: List[str]) -> List[str]:
        """Ensure events is a list of valid events.

        Args:
            value (List[str]): List of event names to validate.

        Returns:
            List[str]: Validated list of event names.

        Raises:
            ServiceException: If any event name in the list is invalid.
        """
        for event in value:
            if event not in WebhookEventEnum.values():
                raise ServiceException(
                    status_code=400,
                    message=f"Invalid event: {event}",
                )
        return value
