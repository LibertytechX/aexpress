import hmac
import hashlib
import json
import requests
import logging
from celery import shared_task
from django.utils import timezone
from .models import WebhookOutbox

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def deliver_webhook_task(self, outbox_id):
    """
    Delivers a webhook payload to the external URL and updates outbox status.
    """
    try:
        outbox = WebhookOutbox.objects.get(id=outbox_id)
    except WebhookOutbox.DoesNotExist:
        logger.error(f"WebhookOutbox record {outbox_id} not found")
        return

    webhook = outbox.webhook
    payload = outbox.payload

    # Generate signature
    payload_str = json.dumps(payload, separators=(",", ":"))
    signature = hmac.new(
        webhook.secret_key.encode("utf-8"), payload_str.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": webhook.event_name,
    }

    try:
        outbox.last_attempt_at = timezone.now()
        response = requests.post(
            webhook.url, data=payload_str, headers=headers, timeout=10
        )

        if 200 <= response.status_code < 300:
            outbox.status = "sent"
            outbox.save()
            logger.info(f"Webhook {outbox_id} sent successfully to {webhook.url}")
        else:
            raise requests.exceptions.HTTPError(f"HTTP {response.status_code}")

    except Exception as e:
        logger.warning(f"Failed to deliver webhook {outbox_id}: {str(e)}")
        outbox.retry_count += 1
        outbox.error_message = str(e)

        if outbox.retry_count >= 3:
            outbox.status = "failed"
            logger.error(f"Webhook {outbox_id} failed after 3 attempts")

        outbox.save()

        # We don't use self.retry(countdown=30) here because we have a dedicated cron
        # but if we wanted immediate retry with backoff, we could.
        # Given the "outbox every 30s" requirement, we'll let the cron handle it.


@shared_task
def webhook_retry_cron():
    """
    Periodic task to retry failed or pending webhooks.
    """
    retryable_records = WebhookOutbox.objects.filter(
        status__in=["pending", "failed"], retry_count__lt=3
    )

    for record in retryable_records:
        # Avoid retrying too soon (at least 30s since last attempt)
        if record.last_attempt_at:
            if (timezone.now() - record.last_attempt_at).total_seconds() < 30:
                continue

        deliver_webhook_task.delay(str(record.id))
