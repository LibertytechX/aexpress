import logging
from .models import Webhook, WebhookOutbox
from .tasks import deliver_webhook_task

logger = logging.getLogger(__name__)


def trigger_webhook(event_name, payload, merchant=None):
    """
    Triggers a webhook for a given event.
    Finds active webhooks, creates outbox records, and schedules delivery.
    """
    event_name = event_name.lower()
    if merchant:
        active_webhooks = Webhook.objects.filter(is_active=True, merchant=merchant)
    else:
        active_webhooks = Webhook.objects.filter(event_name=event_name, is_active=True)

    if not active_webhooks.exists():
        logger.debug(f"No active webhook found for event: {event_name}")
        return

    for webhook in active_webhooks:
        outbox = WebhookOutbox.objects.create(
            webhook=webhook, payload=payload, status="pending"
        )
        if event_name in webhook.events or event_name == webhook.event_name:
            # Immediate delivery attempt in background
            deliver_webhook_task.delay(str(outbox.id))
        else:
            logger.debug(f"Webhook {webhook.id} does not support event: {event_name}")

    logger.info(f"Triggered {active_webhooks.count()} webhooks for event: {event_name}")
