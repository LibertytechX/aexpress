from rest_framework import serializers
from .models import Wallet, Transaction, VirtualAccount
from decimal import Decimal

class WalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet model"""
    user_business_name = serializers.CharField(source='user.business_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'user', 'user_business_name', 'user_phone', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'balance', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""

    class Meta:
        model = Transaction
        fields = [
            'id', 'wallet', 'type', 'amount', 'description', 'reference',
            'balance_before', 'balance_after', 'status', 'paystack_reference',
            'paystack_status', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'wallet', 'balance_before', 'balance_after', 'reference',
            'created_at', 'updated_at'
        ]


class FundWalletSerializer(serializers.Serializer):
    """Serializer for wallet funding request"""
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('100.00'))

    def validate_amount(self, value):
        """Validate amount is at least ₦100"""
        if value < Decimal('100.00'):
            raise serializers.ValidationError("Minimum funding amount is ₦100")
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer for payment verification"""
    reference = serializers.CharField(max_length=100)

    def validate_reference(self, value):
        """Validate reference is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Payment reference is required")
        return value.strip()


class VirtualAccountSerializer(serializers.ModelSerializer):
    """Serializer for VirtualAccount model"""

    class Meta:
        model = VirtualAccount
        fields = [
            'id', 'account_number', 'account_name',
            'bank_name', 'bank_code', 'is_active', 'created_at',
        ]
        read_only_fields = fields

