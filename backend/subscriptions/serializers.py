from rest_framework import serializers
from .models import SubscriptionInvoice, SubscriptionPlan, MerchantSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = "__all__"


class SubscriptionInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionInvoice
        fields = "__all__"


class MerchantSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    invoices = SubscriptionInvoiceSerializer(many=True, read_only=True)

    class Meta:
        model = MerchantSubscription
        fields = "__all__"
