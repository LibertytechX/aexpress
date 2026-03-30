import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


# ── 1. User Signup ──────────────────────────────────────────────────────────
@receiver(post_save, sender="authentication.User")
def on_user_created(sender, instance, created, **kwargs):
    if not created or not instance.phone:
        return
    if instance.usertype not in ("Merchant",):
        return
    from whatsapp_messaging.templates import signup_message
    from whatsapp_messaging.tasks import send_whatsapp_message_task

    text = signup_message(
        instance.contact_name or instance.phone,
        instance.business_name or "your business",
    )
    send_whatsapp_message_task.delay(
        instance.phone, text, "signup", related_user_id=str(instance.id),
    )


# ── 2. Onboarding Complete (email_verified flips to True) ───────────────────
@receiver(pre_save, sender="authentication.User")
def on_user_verified(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    if not old.email_verified and instance.email_verified and instance.phone:
        from whatsapp_messaging.templates import onboarding_message
        from whatsapp_messaging.tasks import send_whatsapp_message_task

        text = onboarding_message(instance.contact_name or instance.phone)
        send_whatsapp_message_task.delay(
            instance.phone, text, "onboarding", related_user_id=str(instance.id),
        )


# ── 3. Order Created ───────────────────────────────────────────────────────
@receiver(post_save, sender="orders.Order")
def on_order_created(sender, instance, created, **kwargs):
    if not created:
        return
    from whatsapp_messaging.templates import order_created_message
    from whatsapp_messaging.tasks import send_whatsapp_message_task

    merchant_phone = instance.user.phone
    if not merchant_phone:
        return
    delivery_count = instance.deliveries.count() or 1
    text = order_created_message(
        instance.order_number,
        instance.pickup_address,
        float(instance.total_amount),
        delivery_count,
    )
    send_whatsapp_message_task.delay(
        merchant_phone, text, "order_created",
        related_order_id=instance.id, related_user_id=str(instance.user_id),
    )


# ── 4 & 5 & 6 & 7. Order Status Changes ────────────────────────────────────
@receiver(pre_save, sender="orders.Order")
def on_order_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    if old.status == instance.status:
        return

    from whatsapp_messaging.tasks import send_whatsapp_message_task
    from whatsapp_messaging import templates

    merchant_phone = instance.user.phone
    new_status = instance.status

    # Rider Assigned → notify merchant + rider
    if new_status == "Assigned" and instance.rider:
        if merchant_phone:
            rider_name = instance.rider.user.contact_name or "Your rider"
            rider_phone = instance.rider.user.phone or ""
            text = templates.rider_assigned_message(
                instance.order_number, rider_name, rider_phone,
            )
            send_whatsapp_message_task.delay(
                merchant_phone, text, "rider_assigned",
                related_order_id=instance.id,
                related_user_id=str(instance.user_id),
            )
        # Notify the rider
        rider_user_phone = instance.rider.user.phone
        if rider_user_phone:
            text = templates.rider_assigned_to_rider_message(
                instance.order_number, instance.pickup_address,
            )
            send_whatsapp_message_task.delay(
                rider_user_phone, text, "rider_assigned",
                related_order_id=instance.id,
                related_user_id=str(instance.rider.user_id),
            )

    # Picked Up → notify merchant
    elif new_status == "Pickup" and merchant_phone:
        text = templates.order_picked_up_message(instance.order_number)
        send_whatsapp_message_task.delay(
            merchant_phone, text, "order_picked_up",
            related_order_id=instance.id,
            related_user_id=str(instance.user_id),
        )

    # Delivered → notify merchant
    elif new_status == "Done" and merchant_phone:
        text = templates.order_delivered_message(instance.order_number)
        send_whatsapp_message_task.delay(
            merchant_phone, text, "order_delivered",
            related_order_id=instance.id,
            related_user_id=str(instance.user_id),
        )

    # Cancelled → notify merchant
    elif new_status in ("CustomerCanceled", "RiderCanceled", "Failed"):
        cancelled_by = "Customer" if new_status == "CustomerCanceled" else "Rider" if new_status == "RiderCanceled" else "System"
        if merchant_phone:
            text = templates.order_cancelled_message(
                instance.order_number, cancelled_by,
            )
            send_whatsapp_message_task.delay(
                merchant_phone, text, "order_cancelled",
                related_order_id=instance.id,
                related_user_id=str(instance.user_id),
            )


# ── 8. Relay Leg Assigned ──────────────────────────────────────────────────
@receiver(pre_save, sender="orders.OrderLeg")
def on_relay_leg_assigned(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    # Rider was just assigned to this leg
    if old.rider_id is None and instance.rider_id is not None:
        from whatsapp_messaging.templates import relay_leg_assigned_message
        from whatsapp_messaging.tasks import send_whatsapp_message_task

        rider_phone = instance.rider.user.phone
        if not rider_phone:
            return
        parent_order_number = instance.order.order_number
        pickup = instance.pickup_address or instance.order.pickup_address
        text = relay_leg_assigned_message(
            parent_order_number, instance.leg_number, pickup,
        )
        send_whatsapp_message_task.delay(
            rider_phone, text, "relay_leg_assigned",
            related_order_id=instance.order_id,
            related_user_id=str(instance.rider.user_id),
        )


# ── 9. Dispatcher/Rider Onboarded ──────────────────────────────────────────
@receiver(post_save, sender="dispatcher.Rider")
def on_rider_created(sender, instance, created, **kwargs):
    if not created:
        return
    from whatsapp_messaging.templates import dispatcher_onboarded_message
    from whatsapp_messaging.tasks import send_whatsapp_message_task

    phone = instance.user.phone
    if not phone:
        return
    text = dispatcher_onboarded_message(
        instance.user.contact_name or phone, phone, "(set via email)",
    )
    send_whatsapp_message_task.delay(
        phone, text, "dispatcher_onboarded",
        related_user_id=str(instance.user_id),
    )


# ── 10. Referral Commission ────────────────────────────────────────────────
@receiver(post_save, sender="wallet.Transaction")
def on_referral_commission(sender, instance, created, **kwargs):
    if not created:
        return
    metadata = instance.metadata or {}
    if metadata.get("type") != "referral_commission":
        return

    from whatsapp_messaging.templates import referral_commission_message
    from whatsapp_messaging.tasks import send_whatsapp_message_task

    rider_phone = instance.wallet.user.phone
    if not rider_phone:
        return
    order_number = metadata.get("order_number", "N/A")
    text = referral_commission_message(
        instance.wallet.user.contact_name or "Rider",
        float(instance.amount),
        order_number,
    )
    send_whatsapp_message_task.delay(
        rider_phone, text, "referral_commission",
        related_user_id=str(instance.wallet.user_id),
    )
