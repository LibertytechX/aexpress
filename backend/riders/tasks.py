import base64
import io
import logging
import asyncio
from celery import shared_task
from django.conf import settings
from ably import AblyRest
from .models import OrderOffer
from .serializers import OrderOfferListSerializer

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def finalize_rider_document_upload_task(self, document_id, file_data, filename):
    """
    Background task: uploads a rider KYC document to S3 and attaches the resulting
    URL to the already-created RiderDocument record. Runs after the view has
    already responded, so the caller never waits on this.
    file_data is base64-encoded file bytes — Celery tasks can't accept file-like objects.
    """
    from dispatcher.s3_utils import upload_document_to_s3
    from .models import RiderDocument

    try:
        document = RiderDocument.objects.get(pk=document_id)
    except RiderDocument.DoesNotExist:
        logger.error(
            f"finalize_rider_document_upload_task: document {document_id} not found"
        )
        return

    file_content = base64.b64decode(file_data)
    file_obj = io.BytesIO(file_content)
    file_url = upload_document_to_s3(file_obj, filename, "riders", document.doc_type)
    if not file_url:
        logger.error(
            f"finalize_rider_document_upload_task: S3 upload failed for document {document_id}"
        )
        raise RuntimeError(f"S3 upload failed for document {document_id}")

    document.file_url = file_url
    document.save(update_fields=["file_url", "updated_at"])


@shared_task
def publish_random_order_offer():
    """
    Pick a random pending OrderOffer and publish to Ably topic 'for-you'.
    Runs every minute via Celery Beat.
    """
    try:
        # Get a random pending offer
        offer = (
            OrderOffer.objects.filter(
                status="pending", rider__isnull=True, order__status="Pending"
            )
            .order_by("?")
            .first()
        )

        if not offer:
            logger.info("No pending order offers found to publish.")
            return False

        # Serialize the offer using the mobile-app format
        serializer = OrderOfferListSerializer(offer)
        payload = serializer.data

        # Publish to Ably
        api_key = getattr(settings, "ABLY_API_KEY", "")
        if not api_key:
            logger.warning(
                "publish_random_order_offer: ABLY_API_KEY not configured, skipping publish"
            )
            return False

        async def _publish():
            client = AblyRest(api_key)
            channel = client.channels.get("for-you")
            await channel.publish("new_offer", payload)

        try:
            asyncio.run(_publish())
            logger.info(
                f"Published random order offer {offer.id} (Order: {offer.order.order_number}) to 'for-you' channel."
            )
            return True
        except Exception as exc:
            logger.error(
                f"publish_random_order_offer: Ably publish failed for offer {offer.id}: {exc}"
            )
            return False

    except Exception as e:
        logger.error(f"Error in publish_random_order_offer: {str(e)}")
        return False
