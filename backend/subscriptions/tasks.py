import logging
from celery import shared_task
from django.utils import timezone
from .models import MerchantSubscription, SubscriptionInvoice
from .services import generate_end_of_period_invoice
from wallet.models import Wallet

logger = logging.getLogger(__name__)


@shared_task(name="subscriptions.tasks.process_subscription_invoicing")
def process_subscription_invoicing():
    """
    Daily task to find subscriptions that have ended and generate invoices.
    """
    now = timezone.now()
    # Find active subscriptions that have passed their end_date and don't have a pending invoice for this period
    ending_subscriptions = MerchantSubscription.objects.filter(
        status="active",
        end_date__lte=now,
    )

    count = 0
    for sub in ending_subscriptions:
        # Check if invoice already exists for this cycle (simple check by date)
        if not SubscriptionInvoice.objects.filter(
            subscription=sub, created_at__gte=sub.start_date
        ).exists():
            invoice = generate_end_of_period_invoice(sub)
            process_invoice_payment.delay(str(invoice.id))
            count += 1

            # Here we might also want to rotate the cycle if auto-renew is enabled
            # For now, we just mark it as ended/expired or keep it active if we want to auto-renew
            # sub.status = "expired"
            # sub.save(update_fields=["status"])

    logger.info(f"Generated {count} subscription invoices.")
    return count


@shared_task(name="subscriptions.tasks.process_invoice_payment")
def process_invoice_payment(invoice_id):
    """
    Attempt to pay a subscription invoice from the merchant's wallet.
    """
    try:
        invoice = SubscriptionInvoice.objects.get(id=invoice_id)
        if invoice.status == "paid":
            return True

        merchant_user = invoice.subscription.merchant.user
        wallet = getattr(merchant_user, "wallet", None)

        if not wallet:
            logger.error(
                f"Merchant {merchant_user.id} has no wallet for invoice {invoice_id}"
            )
            invoice.status = "failed"
            invoice.save(update_fields=["status"])
            return False

        if wallet.balance >= invoice.total_amount:
            wallet.debit(
                amount=invoice.total_amount,
                description=f"Subscription Payment: {invoice.subscription.plan.name}",
                reference=f"SUB-INV-{invoice.id.hex[:12].upper()}",
                metadata={"invoice_id": str(invoice.id)},
            )
            invoice.status = "paid"
            invoice.save(update_fields=["status"])

            # Mark subscription as paid if it's the base plan invoice
            sub = invoice.subscription
            sub.is_paid = True
            sub.save(update_fields=["is_paid"])

            logger.info(f"Paid invoice {invoice_id} from wallet for merchant {merchant_user.id}")
            return True
        else:
            logger.warning(
                f"Insufficient funds for invoice {invoice_id} (Merchant {merchant_user.id}). "
                "Merchant must pay via dynamic virtual account."
            )
            # We leave it as pending (default) so they can pay via virtual account
            invoice.status = "pending"
            invoice.save(update_fields=["status"])
            return False

    except SubscriptionInvoice.DoesNotExist:
        logger.error(f"Invoice {invoice_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error processing payment for invoice {invoice_id}: {e}")
        return False
