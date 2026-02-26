import logging
import asyncio
from celery import shared_task
from django.conf import settings
from ably import AblyRest
from .models import OrderOffer
from .serializers import OrderOfferListSerializer

logger = logging.getLogger(__name__)


@shared_task
def publish_random_order_offer():
    """
    Pick a random pending OrderOffer and publish to Ably topic 'for-you'.
    Runs every minute via Celery Beat.
    """
    try:
        # Get a random pending offer
        offer = OrderOffer.objects.filter(status="pending").order_by("?").first()

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
