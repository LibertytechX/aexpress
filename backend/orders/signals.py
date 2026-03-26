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

    rider = instance.rider

    # 1. Update streak
    try:
        from riders.gamification import update_rider_streak

        update_rider_streak(rider)
    except Exception:
        import traceback

        traceback.print_exc()

    # 2. Update challenge progress
    try:
        from riders.gamification import update_challenge_progress

        update_challenge_progress(rider, instance)
    except Exception:
        import traceback

        traceback.print_exc()

    # 3. Fire referral commission
    try:
        from referrals.services import fire_referral_commission

        fire_referral_commission(instance)

    except Exception:
        import traceback

        traceback.print_exc()

    # 4. Fire buddy referral commission (LibertyPay)
    try:
        if instance.user.referral_code:
            from referrals.tasks import send_buddy_referral_commission_task

            send_buddy_referral_commission_task.delay(
                instance.user.referral_code, instance.order_number
            )
    except Exception:
        import traceback

        traceback.print_exc()
