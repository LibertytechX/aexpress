from dispatcher.models import SystemSettings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order
from riders.models import OrderOffer
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


@receiver(post_save, sender=Order)
def create_order_offer(sender, instance, created, **kwargs):
    if created:
        from .tasks import process_order_proximity

        # Trigger background task for geocoding and zone assignment
        process_order_proximity.delay(instance.id)


@receiver(pre_save, sender=Order)
def track_order_status_change(sender, instance, **kwargs):
    """Store previous status on the instance so post_save can detect transitions."""
    if instance.pk:
        try:
            instance._previous_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Order)
def on_order_completed(sender, instance, created, **kwargs):
    """
    Fires when an Order transitions to 'Done'.
    Triggers: streak update, challenge progress, referral commission.
    All in a background-safe try/except so a gamification failure
    never affects the main order flow.
    """
    if created:
        return

    previous = getattr(instance, "_previous_status", None)
    if instance.status != "Done" or previous == "Done":
        return

    if not instance.rider:
        return

    from .tasks import handle_order_completion_tasks

    # Offload streaks, challenges, and commissions to background task
    handle_order_completion_tasks.delay(instance.id)


@receiver(post_save, sender="orders.MerchantPriceList")
def update_merchant_pricelist_flag(sender, instance, created, **kwargs):
    """
    Auto-toggle the Merchant.has_price_list flag when a price list is created.
    """
    if created:
        from dispatcher.models import Merchant

        # Find the merchant profile for this user
        Merchant.objects.filter(user=instance.merchant).update(has_price_list=True)
