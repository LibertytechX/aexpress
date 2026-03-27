import logging
from django.utils import timezone
from django.db import models
from decimal import Decimal
import datetime
from .models import (
    MerchantSubscription,
    SubscriptionUsage,
    SubscriptionOverage,
    SubscriptionInvoice,
)

logger = logging.getLogger(__name__)


def get_active_subscription(merchant):
    """Retrieve the current active subscription for a merchant."""
    return (
        MerchantSubscription.objects.filter(
            merchant=merchant,
            status="active",
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now(),
        )
        .select_related("plan")
        .first()
    )


def process_order_subscription(order):
    """
    Apply subscription benefits to an order.
    - If within free limit, set total_amount to 0 and increment usage.
    - If over limit, record an overage and set total_amount to 0 (deferred billing).
    """
    merchant_profile = getattr(order.user, "merchant_profile", None)
    if not merchant_profile:
        return None

    subscription = get_active_subscription(merchant_profile)
    if not subscription:
        return None

    plan = subscription.plan

    # Get or create usage for the current cycle
    usage, created = SubscriptionUsage.objects.get_or_create(
        subscription=subscription,
        cycle_start_date=subscription.start_date.date(),
        cycle_end_date=subscription.end_date.date(),
    )

    if usage.used_free_orders < plan.free_orders_limit:
        # Covered by free orders
        usage.used_free_orders += 1
        usage.save(update_fields=["used_free_orders"])
        order.total_amount = Decimal("0.00")
        logger.info(f"Order {order.order_number} covered by subscription free limit.")
    else:
        # Overage - record for deferred billing
        SubscriptionOverage.objects.create(
            subscription=subscription,
            order=order,
            amount=plan.overage_fee,
        )
        order.total_amount = Decimal("0.00")
        logger.info(f"Order {order.order_number} recorded as subscription overage.")

    return subscription


def generate_end_of_period_invoice(subscription):
    """
    Generate an invoice at the end of the subscription billing cycle.
    Sums the base plan amount and all overages.
    """
    overages = SubscriptionOverage.objects.filter(subscription=subscription)
    total_overage_amount = (
        overages.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")
    )

    plan_amount = subscription.plan.price
    total_amount = plan_amount + total_overage_amount

    invoice = SubscriptionInvoice.objects.create(
        subscription=subscription,
        plan_amount=plan_amount,
        total_overage_amount=total_overage_amount,
        total_amount=total_amount,
        status="pending",
    )

    # Initial virtual account generation
    refresh_invoice_virtual_account(invoice)

    logger.info(
        f"Generated invoice for subscription {subscription.id}: Total {total_amount}"
    )
    return invoice


def refresh_invoice_virtual_account(invoice):
    """
    Generate or refresh a one-time virtual account for an invoice.
    TTL is 30 minutes.
    """
    from wallet.corebanking_service import generate_one_time_account

    # Check if existing one is still valid (within 30 mins)
    if invoice.payment_info and invoice.virtual_account_expiry:
        if timezone.now() < invoice.virtual_account_expiry:
            return True

    # Generate new reference (includes timestamp to ensure uniqueness and new account)
    payment_ref = f"SUB-INV-{invoice.id.hex[:10].upper()}-{int(timezone.now().timestamp())}"

    success, account_data = generate_one_time_account(payment_ref)
    if success:
        invoice.payment_ref = payment_ref
        invoice.payment_info = account_data
        invoice.virtual_account_expiry = timezone.now() + datetime.timedelta(minutes=30)
        invoice.save(
            update_fields=["payment_ref", "payment_info", "virtual_account_expiry", "updated_at"]
        )
        return True

    logger.error(f"Failed to refresh virtual account for invoice {invoice.id}: {account_data}")
    return False


def get_dedicated_rider(merchant):
    """Retrieve the dedicated rider for a merchant if they have the benefit."""
    from .models import MerchantDedicatedRider

    # Check if merchant has an active subscription with dedicated rider benefit
    subscription = get_active_subscription(merchant)
    if not subscription or not subscription.plan.has_dedicated_rider:
        return None

    dedicated_rider_rel = MerchantDedicatedRider.objects.filter(
        merchant=merchant
    ).first()
    if dedicated_rider_rel:
        return dedicated_rider_rel.rider
    return None
