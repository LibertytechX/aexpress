from typing import Any
from dispatcher.models import SystemSettings
from django.db.models.signals import post_save, pre_save
from django.dispatch import Signal, receiver
from .models import Order, OrderEvent
from riders.models import OrderOffer
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Custom signal for dispatching arbitrary order events
order_event_signal: Signal = Signal()


@receiver(post_save, sender=Order)
def create_order_offer(sender, instance, created, **kwargs):
    if created:
        from .tasks import process_order_proximity

        # Trigger background task for geocoding and zone assignment
        process_order_proximity.delay(instance.id)


@receiver(post_save, sender=Order)
def notify_dispatchers_on_new_order(
    sender: Any, instance: Order, created: bool, **kwargs: Any
) -> None:
    """Signal receiver to trigger email notifications to all active dispatchers when an order is created.

    Args:
        sender (Any): The model class.
        instance (Order): The actual order instance being saved.
        created (bool): A boolean; True if a new record was created.
        **kwargs (Any): Additional keyword arguments.
    """
    if created:
        from .tasks import send_new_order_dispatcher_email_task

        send_new_order_dispatcher_email_task.delay(str(instance.id))


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


@receiver(post_save, sender=Order)
def send_merchant_email_on_status_change(sender, instance, created, **kwargs):
    """
    Triggers email notifications to the merchant on order progression stages.
    """
    if created:
        from .tasks import send_transactional_email

        send_transactional_email.delay("F_Pending", str(instance.id))
        return

    previous_status = getattr(instance, "_previous_status", None)
    current_status = instance.status

    if previous_status != current_status:
        from .tasks import send_transactional_email

        status_template_map = {
            "Assigned": "F_Assigned",
            "AssignmentAccepted": "F_AssignmentAccepted",
            "Started": "F1",
            "Pickup": "F_PickedUp",
            "PickedUp": "F_PickedUp",
            "Fulfilling": "F_Fulfilling",
            "Arrived": "F_Arrived",
            "Done": "F2",
            "CustomerCanceled": "F_CustomerCanceled",
            "RiderCanceled": "F_RiderCanceled",
            "Failed": "F_Failed",
        }

        template_code = status_template_map.get(current_status)
        if template_code:
            send_transactional_email.delay(template_code, str(instance.id))


@receiver(post_save, sender=Order)
def log_order_event_on_created(
    sender: Any, instance: Order, created: bool, **kwargs: Any
) -> None:
    """Automatically create an OrderEvent log when a new Order is created.

    Args:
        sender (Any): The model class sending the signal.
        instance (Order): The Order instance created.
        created (bool): Indicates if a new record was created.
        **kwargs (Any): Additional keyword arguments.
    """
    if created:
        OrderEvent.objects.create(
            order=instance,
            event="order_created",
            description=f"Order #{instance.order_number} created with status '{instance.status}'.",
            created_by=getattr(instance, "user", None),
        )


@receiver(post_save, sender=Order)
def log_order_event_on_status_change(
    sender: Any, instance: Order, created: bool, **kwargs: Any
) -> None:
    """Automatically create an OrderEvent log when an Order status changes.

    Args:
        sender (Any): The model class sending the signal.
        instance (Order): The Order instance being updated.
        created (bool): Indicates if a new record was created.
        **kwargs (Any): Additional keyword arguments.
    """
    if created:
        return

    previous_status = getattr(instance, "_previous_status", None)
    current_status = instance.status

    if previous_status and previous_status != current_status:
        OrderEvent.objects.create(
            order=instance,
            event=f"order_status_{current_status.lower()}",
            description=f"Order status updated from {previous_status} to {current_status}.",
            old_value=str(previous_status),
            new_value=str(current_status),
        )


@receiver(order_event_signal)
def handle_custom_order_event(
    sender: Any,
    order: Order,
    event: str,
    description: str,
    old_value: str = "",
    new_value: str = "",
    created_by: Any = None,
    **kwargs: Any,
) -> None:
    """Receiver for custom OrderEvent signals.

    Args:
        sender (Any): Sender of the signal.
        order (Order): Target order.
        event (str): Event title/identifier.
        description (str): Event detailed description.
        old_value (str): Old attribute value if applicable.
        new_value (str): New attribute value if applicable.
        created_by (Any): User who triggered the event.
        **kwargs (Any): Additional keyword arguments.
    """
    OrderEvent.objects.create(
        order=order,
        event=event,
        description=description,
        old_value=old_value,
        new_value=new_value,
        created_by=created_by,
    )
