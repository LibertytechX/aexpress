import asyncio
import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from riders.models import OrderOffer
from riders.serializers import OrderOfferListSerializer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Pick a random pending OrderOffer and publish it to the Ably 'for-you' channel."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--channel",
            type=str,
            default="for-you",
            help="Ably channel name to publish to (default: for-you)",
        )
        parser.add_argument(
            "--event",
            type=str,
            default="new_offer",
            help="Ably event name (default: new_offer)",
        )

    def handle(self, *args, **options):
        channel_name = options["channel"]
        event_name = options["event"]

        # 1. Grab a random pending offer
        offer = OrderOffer.objects.filter(status="pending").order_by("?").first()
        if not offer:
            self.stdout.write(self.style.WARNING("No pending OrderOffers found."))
            return

        self.stdout.write(
            f"Selected offer: {offer.id} (Order: {offer.order.order_number})"
        )

        # 2. Serialize to the mobile-app payload format
        serializer = OrderOfferListSerializer(offer)
        payload = serializer.data
        self.stdout.write("Payload to publish:")
        self.stdout.write(json.dumps(dict(payload), indent=2, default=str))

        # 3. Publish to Ably
        api_key = getattr(settings, "ABLY_API_KEY", "")
        if not api_key:
            self.stdout.write(
                self.style.ERROR("ABLY_API_KEY is not configured in settings.")
            )
            return

        async def _publish():
            from ably import AblyRest

            client = AblyRest(api_key)
            channel = client.channels.get(channel_name)
            await channel.publish(event_name, dict(payload))

        try:
            asyncio.run(_publish())
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully published offer {offer.id} to channel '{channel_name}' "
                    f"(event: '{event_name}')."
                )
            )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Ably publish failed: {exc}"))
            raise
