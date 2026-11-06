import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_whatsapp_message_task(self, phone_number, text, event_type,
                                related_order_id=None, related_user_id=None,
                                media_url=None):
    """
    Async task to send a WhatsApp message and log the result.
    """
    from whatsapp_messaging.models import WhatsAppMessage
    from whatsapp_messaging.service import send_message

    # Create the log record
    msg_log = WhatsAppMessage.objects.create(
        recipient_phone=phone_number,
        event_type=event_type,
        message_content=text,
        status=WhatsAppMessage.Status.PENDING,
        related_order_id=related_order_id,
        related_user_id=related_user_id,
    )

    result = send_message(phone_number, text, media_url=media_url)

    if result["success"]:
        msg_log.status = WhatsAppMessage.Status.SENT
        msg_log.external_message_id = result["message_id"]
        msg_log.sent_at = timezone.now()
        msg_log.save(update_fields=["status", "external_message_id", "sent_at"])
    else:
        msg_log.status = WhatsAppMessage.Status.FAILED
        msg_log.error_message = result["error"]
        msg_log.save(update_fields=["status", "error_message"])
        logger.warning(
            f"WhatsApp send failed for {phone_number} [{event_type}]: {result['error']}"
        )
        # Retry on failure
        try:
            self.retry()
        except self.MaxRetriesExceededError:
            logger.error(
                f"WhatsApp max retries exceeded for {phone_number} [{event_type}]"
            )
