from .models import (
    SubscriptionInvoice,
    SubscriptionPlan,
    MerchantSubscription,
    PostpaidPlan,
    MerchantPostpaidSubscription,
    PostpaidInvoice,
)
from rest_framework import serializers


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


class PostpaidPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostpaidPlan
        fields = "__all__"


class PostpaidInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostpaidInvoice
        fields = "__all__"


class MerchantPostpaidSubscriptionSerializer(serializers.ModelSerializer):
    plan = PostpaidPlanSerializer(read_only=True)
    invoices = PostpaidInvoiceSerializer(many=True, read_only=True)

    class Meta:
        model = MerchantPostpaidSubscription
        fields = "__all__"
