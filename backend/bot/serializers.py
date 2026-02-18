"""
Serializers for WhatsApp bot API.
Bot-friendly versions with conversational responses.
"""
from rest_framework import serializers
from authentication.models import User
from orders.models import Order, Delivery, Vehicle
from wallet.models import Transaction
from .utils import format_currency, format_order_summary


class BotMerchantProfileSerializer(serializers.ModelSerializer):
    """Simplified merchant profile for bot responses."""
    wallet_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'business_name', 'contact_name', 'phone', 'email', 'wallet_balance']
    
    def get_wallet_balance(self, obj):
        return obj.wallet.balance if hasattr(obj, 'wallet') else 0


class BotQuickSignupSerializer(serializers.Serializer):
    """Passwordless signup for WhatsApp bot."""
    phone = serializers.CharField(required=True)
    business_name = serializers.CharField(required=True, max_length=255)
    contact_name = serializers.CharField(required=True, max_length=255)
    business_address = serializers.CharField(required=False, allow_blank=True)
    industry = serializers.CharField(required=False, allow_blank=True)


class BotOrderSerializer(serializers.ModelSerializer):
    """Simplified order details for bot."""
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    formatted_amount = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'order_number', 'status', 'status_display', 'mode',
            'pickup_address', 'sender_name', 'sender_phone',
            'vehicle_name', 'total_amount', 'formatted_amount',
            'created_at', 'summary'
        ]
    
    def get_formatted_amount(self, obj):
        return format_currency(obj.total_amount)
    
    def get_summary(self, obj):
        return format_order_summary(obj)


class BotTransactionSerializer(serializers.ModelSerializer):
    """Simplified transaction for bot."""
    formatted_amount = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'reference', 'type', 'type_display', 'amount', 'formatted_amount',
            'description', 'status', 'created_at'
        ]
    
    def get_formatted_amount(self, obj):
        return format_currency(obj.amount)


class BotPriceQuoteSerializer(serializers.Serializer):
    """Request price quote for delivery."""
    pickup_address = serializers.CharField(required=True)
    dropoff_address = serializers.CharField(required=True)
    vehicle_type = serializers.CharField(required=False, allow_blank=True)


class BotCreateOrderSerializer(serializers.Serializer):
    """Create order via bot."""
    pickup_address = serializers.CharField(required=True)
    dropoff_address = serializers.CharField(required=True)
    vehicle_type = serializers.CharField(required=True)  # bike, car, van
    pickup_contact_name = serializers.CharField(required=True)
    pickup_contact_phone = serializers.CharField(required=True)
    dropoff_contact_name = serializers.CharField(required=True)
    dropoff_contact_phone = serializers.CharField(required=True)
    package_type = serializers.CharField(required=False, default='parcel')
    pickup_notes = serializers.CharField(required=False, allow_blank=True)
    dropoff_notes = serializers.CharField(required=False, allow_blank=True)


class BotVehicleSerializer(serializers.ModelSerializer):
    """Vehicle pricing for bot."""
    formatted_base_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = ['id', 'name', 'base_price', 'formatted_base_price', 'rate_per_km', 'rate_per_minute']
    
    def get_formatted_base_price(self, obj):
        return format_currency(obj.base_price)

