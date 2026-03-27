from email.policy import default
from django.db import models
from django.conf import settings
import uuid


class SubscriptionPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    free_orders_limit = models.PositiveIntegerField(default=0)
    order_credits = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_order_km = models.FloatField(default=0.0)
    overage_fee = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="overage fee percentage"
    )
    has_dedicated_rider = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscription_plans"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} (₦{self.price})"

    def save(self, *args, **kwargs):
        if self.order_credits <= 0:
            self.order_credits = self.price / 100
        super().save(*args, **kwargs)


class MerchantSubscription(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        "dispatcher.Merchant", on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    is_paid = models.BooleanField(default=False)
    plan_credit = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "merchant_subscriptions"
        ordering = ["-created_at"]

    def __str__(self):
        business_name = (
            getattr(self.merchant.user, "business_name", None)
            or self.merchant.merchant_id
        )
        return f"{business_name} - {self.plan.name}"

    def has_sufficient_credit(self, amount):
        return self.plan_credit >= float(amount)

    def save(self, *args, **kwargs):
        if self.plan_credit <= 0:
            self.plan_credit = self.plan.order_credits
        super().save(*args, **kwargs)

    def deduct_credit(self, amount):
        from django.db import transaction

        with transaction.atomic():
            # Refresh from DB with a row lock to prevent race conditions
            locked_subscription = MerchantSubscription.objects.select_for_update().get(
                pk=self.pk
            )
            if locked_subscription.plan_credit >= float(amount):
                locked_subscription.plan_credit -= float(amount)
                locked_subscription.save(update_fields=["plan_credit"])
                # Sync the current instance
                self.plan_credit = locked_subscription.plan_credit
                return True
            return False


class SubscriptionUsage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        MerchantSubscription, on_delete=models.CASCADE, related_name="usages"
    )
    cycle_start_date = models.DateField()
    cycle_end_date = models.DateField()
    used_free_orders = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "subscription_usages"


class SubscriptionOverage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        MerchantSubscription, on_delete=models.CASCADE, related_name="overages"
    )
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subscription_overages"


class SubscriptionInvoice(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        MerchantSubscription, on_delete=models.PROTECT, related_name="invoices"
    )
    plan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_overage_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_ref = models.CharField(max_length=100, null=True, blank=True, unique=True)
    payment_info = models.JSONField(null=True, blank=True)
    virtual_account_expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscription_invoices"
        ordering = ["-created_at"]


class MerchantDedicatedRider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        "dispatcher.Merchant", on_delete=models.CASCADE, related_name="dedicated_riders"
    )
    rider = models.ForeignKey("dispatcher.Rider", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "merchant_dedicated_riders"
        unique_together = ("merchant", "rider")
