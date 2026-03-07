import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class RiderReferral(models.Model):
    """
    Links a referring rider to a merchant they brought onto the platform.
    A referral is 'pending' until the merchant completes their first order,
    at which point it becomes 'active'.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referring_rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.CASCADE,
        related_name="referrals",
    )
    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referred_by",
        help_text="The merchant (business) user that was referred.",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set when the merchant completes their first order.",
    )

    class Meta:
        db_table = "rider_referrals"
        unique_together = ("referring_rider", "merchant")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Referral: {self.referring_rider.rider_id} → {self.merchant.business_name} [{self.status}]"

    def get_monthly_stats(self):
        """Returns orders count and earnings for this referral in the current month."""
        from decimal import Decimal

        today = timezone.now().date()
        month_start = today.replace(day=1)
        earnings = self.earnings.filter(created_at__date__gte=month_start).aggregate(
            total=models.Sum("commission_amount")
        )["total"] or Decimal("0.00")
        orders = self.earnings.filter(created_at__date__gte=month_start).count()
        return {"orders_this_month": orders, "earnings_this_month": earnings}


class ReferralEarning(models.Model):
    """
    One record per order that comes from a referred merchant.
    Records the 5% commission credited to the referring rider's wallet.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referral = models.ForeignKey(
        RiderReferral,
        on_delete=models.CASCADE,
        related_name="earnings",
    )
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="referral_earning",
    )
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="5% of the order's total_amount.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "referral_earnings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commission ₦{self.commission_amount} — Order {self.order.order_number}"
