from firebase_admin import messaging
from .models import RiderDevice, RiderNotification
import logging
import firebase_admin

logger = logging.getLogger(__name__)


def send_push(token, title, body, data=None):
    """
    Send a push notification to a specific FCM token.
    """
    if not firebase_admin._apps:
        logger.warning("Firebase not initialized. Push notification skipped.")
        return None

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        data=data or {},
    )

    try:
        response = messaging.send(message)
        logger.info(f"Successfully sent message: {response}")
        return response
    except Exception as e:
        logger.error(f"Error sending Firebase notification: {e}")
        return None


def notify_rider(rider, title, body, data=None):
    """
    Send a push notification to all active devices of a rider and persist it.
    """
    # 1. Persist the notification
    RiderNotification.objects.create(
        rider=rider, title=title, body=body, data=data or {}
    )

    # 2. Get all active FCM tokens for the rider
    devices = RiderDevice.objects.filter(rider=rider, is_active=True).exclude(
        fcm_token=""
    )
    tokens = devices.values_list("fcm_token", flat=True)

    if not tokens:
        logger.info(f"No active FCM tokens found for rider {rider.rider_id}")
        return

    # 3. Send to each token
    for token in tokens:
        send_push(token, title, body, data)
