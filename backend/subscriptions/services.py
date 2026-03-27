import logging
from django.utils import timezone
from django.db import models, transaction
from decimal import Decimal
import datetime
from .models import (
    MerchantSubscription,
    SubscriptionUsage,
    SubscriptionOverage,
    SubscriptionInvoice,
    PostpaidPlan,
    MerchantPostpaidSubscription,
    PostpaidInvoice,
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
    - If merchant has credits, deduct from plan_credit.
    - If credits exhausted, record an overage and apply overage fee percentage.
    """
    merchant_profile = getattr(order.user, "merchant_profile", None)
    if not merchant_profile:
        return None

    subscription = get_active_subscription(merchant_profile)
    if not subscription:
        return None

    plan = subscription.plan
    order_amount = order.total_amount
    order_amount_in_credit = round(order.total_amount / 100, 2)

    if subscription.has_sufficient_credit(amount=order_amount_in_credit):
        # Deduct credits
        if subscription.deduct_credit(amount=order_amount_in_credit):
            # usage tracking
            usage, created = SubscriptionUsage.objects.get_or_create(
                subscription=subscription,
                cycle_start_date=subscription.start_date.date(),
                cycle_end_date=subscription.end_date.date(),
            )
            usage.used_free_orders += 1
            usage.save(update_fields=["used_free_orders"])

            logger.info(f"Order {order.order_number} covered by subscription credits.")
            return subscription

    # If we are here, credits are insufficient - record as overage
    # For overage, we might want to apply a fee based on the order amount and plan's overage_fee percentage
    # (Assuming overage_fee is a percentage based on user's help_text)
    # overage_amount = order.total_amount * (plan.overage_fee / Decimal("100.00"))
    # check if the credit is still left
    if subscription.plan_credit > 0:
        order_amount = order_amount - (subscription.plan_credit * 100)
        subscription.deduct_credit(amount=subscription.plan_credit)

    SubscriptionOverage.objects.create(
        subscription=subscription,
        order=order,
        amount=order_amount,
    )
    order.payment_status = "Paid"
    order.save()
    logger.info(
        f"Order {order.order_number} recorded as subscription overage ({plan.overage_fee}% fee)."
    )
    return subscription


def generate_end_of_period_invoice(subscription):
    """
    Generate an invoice at the end of the subscription billing cycle.
    Sums the base plan amount and all overages.
    """
    overages = SubscriptionOverage.objects.filter(subscription=subscription)
    total_overage_amount = overages.aggregate(total=models.Sum("amount"))[
        "total"
    ] or Decimal("0.00")

    plan_amount = subscription.plan.price
    total_amount = plan_amount + total_overage_amount

    invoice, created = SubscriptionInvoice.objects.update_or_create(
        subscription=subscription,
        status="pending",  # Only update if it hasn't been paid yet
        defaults={
            "plan_amount": plan_amount,
            "total_overage_amount": total_overage_amount,
            "total_amount": total_amount,
        },
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
    payment_ref = (
        f"SUB-INV-{invoice.id.hex[:10].upper()}-{int(timezone.now().timestamp())}"
    )

    success, account_data = generate_one_time_account(payment_ref)
    if success:
        invoice.payment_ref = payment_ref
        invoice.payment_info = account_data
        invoice.virtual_account_expiry = timezone.now() + datetime.timedelta(minutes=30)
        invoice.save(
            update_fields=[
                "payment_ref",
                "payment_info",
                "virtual_account_expiry",
                "updated_at",
            ]
        )
        return True

    logger.error(
        f"Failed to refresh virtual account for invoice {invoice.id}: {account_data}"
    )
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


def activate_merchant_subscription(merchant, plan):
    """
    Activate a subscription for a merchant.
    - If they have an existing active one, generate final invoice and mark as expired.
    - Create a new active MerchantSubscription.
    - Update the Merchant model flag.
    """
    # Create new subscription
    start_date = timezone.now()
    end_date = start_date + datetime.timedelta(days=30)

    subscription = MerchantSubscription.objects.create(
        merchant=merchant,
        plan=plan,
        start_date=start_date,
        end_date=end_date,
        status="active",
        is_paid=False,  # Base fee is included in the end-of-period invoice
    )

    # Update Merchant flag
    merchant.has_active_subscription = True
    merchant.save(update_fields=["has_active_subscription", "updated_at"])
    # generate_end_of_period_invoice(subscription)

    logger.info(
        f"Activated {plan.name} subscription for merchant {merchant.merchant_id}"
    )
    return subscription


def get_active_postpaid_subscription(merchant):
    """Retrieve the current active postpaid subscription for a merchant."""
    return (
        MerchantPostpaidSubscription.objects.filter(
            merchant=merchant, status__in=["active", "blocked"]
        )
        .select_related("plan")
        .first()
    )


def accumulate_postpaid_order(order):
    """
    Add order total to merchant's postpaid accumulated amount.
    """
    merchant_profile = getattr(order.user, "merchant_profile", None)
    if not merchant_profile:
        return False

    subscription = get_active_postpaid_subscription(merchant_profile)
    if not subscription:
        return False

    if subscription.status == "blocked":
        # Blocked merchants cannot accumulate more until payment
        return False

    with transaction.atomic():
        # Lock the row for update to prevent race conditions
        subscription = MerchantPostpaidSubscription.objects.select_for_update().get(
            id=subscription.id
        )
        subscription.accumulated_amount += order.total_amount
        subscription.save(update_fields=["accumulated_amount", "updated_at"])

    order.payment_status = "Postpaid"
    order.save(update_fields=["payment_status"])
    return True


def generate_postpaid_invoice(subscription):
    """
    Generate an invoice for the current postpaid period.
    """
    amount = subscription.accumulated_amount
    if amount <= 0:
        # Just rotate the period if no accumulation
        _rotate_postpaid_period(subscription)
        return None

    due_date = timezone.now() + datetime.timedelta(days=1)  # 24h grace period

    invoice = PostpaidInvoice.objects.create(
        subscription=subscription, amount=amount, status="pending", due_date=due_date
    )

    # Reset accumulation and rotate period
    _rotate_postpaid_period(subscription)

    # Generate virtual account for payment
    refresh_postpaid_invoice_virtual_account(invoice)

    # Block merchant until payment is completed
    subscription.status = "blocked"
    subscription.save(update_fields=["status"])

    logger.info(
        f"Generated postpaid invoice {invoice.id} for merchant {subscription.merchant.merchant_id}"
    )
    return invoice


def _rotate_postpaid_period(subscription):
    """Update period start and end dates based on plan type and reset accumulation."""
    now = timezone.now()
    subscription.current_period_start = now
    if subscription.plan.plan_type == "weekly":
        subscription.current_period_end = now + datetime.timedelta(days=7)
    else:
        subscription.current_period_end = now + datetime.timedelta(days=30)

    subscription.accumulated_amount = Decimal("0.00")
    subscription.save(
        update_fields=[
            "current_period_start",
            "current_period_end",
            "accumulated_amount",
            "updated_at",
        ]
    )


def refresh_postpaid_invoice_virtual_account(invoice):
    """
    Generate or refresh a dynamic virtual account for a postpaid invoice.
    """
    from wallet.corebanking_service import generate_one_time_account

    # Generate reference
    payment_ref = (
        f"POST-INV-{invoice.id.hex[:10].upper()}-{int(timezone.now().timestamp())}"
    )

    success, account_data = generate_one_time_account(payment_ref)
    if success:
        invoice.payment_ref = payment_ref
        invoice.payment_info = account_data
        invoice.save(update_fields=["payment_ref", "payment_info", "updated_at"])
        return True

    logger.error(f"Failed to refresh virtual account for postpaid invoice {invoice.id}")
    return False


def handle_postpaid_invoice_paid(invoice):
    """
    Mark invoice as paid and unblock subscription if no other pending invoices exist.
    """
    subscription = invoice.subscription
    invoice.status = "paid"
    invoice.save(update_fields=["status", "updated_at"])

    # Check for other pending invoices
    has_pending = PostpaidInvoice.objects.filter(
        subscription=subscription, status="pending"
    ).exists()
    if not has_pending:
        subscription.status = "active"
        subscription.save(update_fields=["status", "updated_at"])
        logger.info(
            f"Merchant {subscription.merchant.merchant_id} unblocked after paying invoice."
        )
