"""
Serializers for Assured Express (AXpress) AI Agent endpoints.
"""

from typing import Any, Dict
from decimal import Decimal
from rest_framework import serializers
from sparky_utils.exceptions import ServiceException


class QuoteRequestSerializer(serializers.Serializer):
    """Serializer for quote calculation requests."""

    pickup_location = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Pickup street address, landmark, or location string.",
    )
    delivery_location = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Delivery / dropoff address or destination.",
    )
    vehicle = serializers.CharField(
        required=False,
        default="Bike",
        allow_blank=True,
        help_text="Preferred vehicle type (defaults to 'Bike').",
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate location parameters."""
        pickup = attrs.get("pickup_location", "").strip()
        delivery = attrs.get("delivery_location", "").strip()

        if not pickup:
            raise ServiceException(
                status_code=400,
                message="Pickup location cannot be empty.",
            )
        if not delivery:
            raise ServiceException(
                status_code=400,
                message="Delivery location cannot be empty.",
            )

        # Normalize vehicle to title case or default to Bike
        vehicle = (attrs.get("vehicle") or "Bike").strip()
        attrs["vehicle"] = vehicle.title() if vehicle else "Bike"
        return attrs


class AgentBookOrderSerializer(serializers.Serializer):
    """Serializer for creating an order via AI agent / MCP."""

    pickup_address = serializers.CharField(required=True, max_length=500)
    sender_name = serializers.CharField(required=True, max_length=255)
    sender_phone = serializers.CharField(required=True, max_length=30)

    dropoff_address = serializers.CharField(required=True, max_length=500)
    receiver_name = serializers.CharField(required=True, max_length=255)
    receiver_phone = serializers.CharField(required=True, max_length=30)
    receiver_email = serializers.EmailField(required=False, allow_blank=True, default="")

    vehicle = serializers.CharField(required=False, default="Bike")
    package_type = serializers.ChoiceField(
        choices=["Box", "Envelope", "Fragile", "Food", "Document", "Other"],
        default="Box",
        required=False,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    payment_method = serializers.ChoiceField(
        choices=["wallet", "cash", "cash_on_pickup", "receiver_pays", "postpaid"],
        default="wallet",
        required=False,
    )
    scheduled_pickup_time = serializers.DateTimeField(required=False, allow_null=True, default=None)
    collect_on_delivery = serializers.BooleanField(required=False, default=False)
    cod_amount = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=12,
        decimal_places=2,
        default=None,
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order booking details."""
        if attrs.get("collect_on_delivery") and not attrs.get("cod_amount"):
            raise ServiceException(
                status_code=400,
                message="cod_amount is required when collect_on_delivery is true.",
            )

        vehicle = (attrs.get("vehicle") or "Bike").strip()
        attrs["vehicle"] = vehicle.title() if vehicle else "Bike"
        return attrs


class CustomerDeliveriesQuerySerializer(serializers.Serializer):
    """Serializer for customer delivery history queries."""

    phone = serializers.CharField(
        required=True,
        help_text="Customer phone number (sender or receiver).",
    )
    status = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional order status filter (e.g. 'Pending', 'InTransit', 'Done').",
    )
    limit = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=50,
        help_text="Maximum records to return (1-50, default 10).",
    )
