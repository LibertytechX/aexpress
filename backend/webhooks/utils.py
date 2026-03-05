import logging
from .models import Webhook, WebhookOutbox
from .tasks import deliver_webhook_task

logger = logging.getLogger(__name__)


def trigger_webhook(event_name, payload):
    """
    Triggers a webhook for a given event.
    Finds active webhooks, creates outbox records, and schedules delivery.
    """
    event_name = event_name.lower()
    active_webhooks = Webhook.objects.filter(event_name=event_name, is_active=True)

    if not active_webhooks.exists():
        logger.debug(f"No active webhook found for event: {event_name}")
        return

    for webhook in active_webhooks:
        outbox = WebhookOutbox.objects.create(
            webhook=webhook, payload=payload, status="pending"
        )

        # Immediate delivery attempt in background
        deliver_webhook_task.delay(str(outbox.id))

    logger.info(f"Triggered {active_webhooks.count()} webhooks for event: {event_name}")
