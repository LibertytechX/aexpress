import logging

from riders.notifications import send_push

logger = logging.getLogger(__name__)

# Maps the category string passed by callers to the corresponding
# field name on MerchantNotificationSettings.
CATEGORY_FIELD_MAP = {
    "order_assigned": "order_assigned",
    "order_completed": "order_completed",
    "order_cancelled": "order_cancelled",
    "wallet_credit": "wallet_credit",
    "marketing": "marketing",
}


def notify_merchant(merchant_id, title, body, data=None, category="general"):
    """
    Persist a MerchantNotification record and send a push notification to all
    active devices for the given merchant.

    Args:
        merchant_id (str): UUID of the Merchant (dispatcher.Merchant.id).
        title (str): Notification title.
        body (str): Notification body text.
        data (dict | None): Arbitrary key/value payload sent with the push.
        category (str): Matches a toggle field on MerchantNotificationSettings
                        (e.g. "order_assigned", "order_completed"). Defaults to
                        "general" which only checks the master push_enabled switch.

    Notes:
        - The DB record is always created regardless of push toggle state so
          merchants can view their notification history in-app.
        - Push delivery is skipped (not retried) when either push_enabled or
          the category-specific toggle is False.
    """
    from dispatcher.models import Merchant, MerchantNotification, MerchantNotificationSettings

    try:
        merchant = Merchant.objects.select_related("notification_settings").get(id=merchant_id)
    except Merchant.DoesNotExist:
        logger.error(f"notify_merchant: Merchant {merchant_id} not found.")
        return

    # Always persist the notification record.
    MerchantNotification.objects.create(
        merchant=merchant,
        title=title,
        body=body,
        data=data or {},
    )

    # Resolve notification settings (auto-create for merchants pre-dating this feature).
    settings_obj, _ = MerchantNotificationSettings.objects.get_or_create(merchant=merchant)

    # Check master switch first.
    if not settings_obj.push_enabled:
        logger.info(f"Push disabled for merchant {merchant.merchant_id}. Skipping push.")
        return

    # Check category-specific toggle (skip unknown categories gracefully).
    category_field = CATEGORY_FIELD_MAP.get(category)
    if category_field and not getattr(settings_obj, category_field, True):
        logger.info(
            f"Category '{category}' push disabled for merchant {merchant.merchant_id}. Skipping push."
        )
        return

    # Fetch all active device tokens.
    tokens = list(
        merchant.devices.filter(is_active=True).exclude(fcm_token="").values_list("fcm_token", flat=True)
    )

    if not tokens:
        logger.info(f"No active FCM tokens found for merchant {merchant.merchant_id}.")
        return

    for token in tokens:
        send_push(token, title, body, data)
