from rest_framework import serializers

from orders.models import Order
from .models import SupportTicket


class SupportTicketSerializer(serializers.ModelSerializer):
    """
    Rider-facing ticket serializer.
    Riders may optionally link a ticket to one of their own orders via `order_number`.
    """

    order_number = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    order = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "reference",
            "category",
            "subject",
            "message",
            "order_number",
            "order",
            "status",
            "priority",
            "resolution_note",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reference",
            "status",
            "priority",
            "resolution_note",
            "resolved_at",
            "created_at",
            "updated_at",
        ]

    def get_order(self, obj):
        return obj.order.order_number if obj.order else None

    def validate_order_number(self, value):
        if not value:
            return None
        rider = self.context["rider"]
        try:
            return Order.objects.get(order_number=value, rider=rider)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found for this rider.")

    def create(self, validated_data):
        validated_data["order"] = validated_data.pop("order_number", None)
        validated_data["rider"] = self.context["rider"]
        return super().create(validated_data)
