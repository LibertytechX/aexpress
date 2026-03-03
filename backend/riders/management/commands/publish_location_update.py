import asyncio
import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Publish a mock location update to the Ably 'location-update' channel."

    def add_arguments(self, parser):
        parser.add_argument(
            "--channel",
            type=str,
            default="location-update",
            help="Ably channel name to publish to (default: location-update)",
        )
        parser.add_argument(
            "--event",
            type=str,
            default="location-update",
            help="Ably event name (default: location-update)",
        )
        parser.add_argument(
            "--rider",
            type=str,
            default="rider-123",
            help="Rider ID to send in the payload",
        )
        parser.add_argument(
            "--latitude",
            type=float,
            default=37.4219983,
            help="Latitude to send in the payload",
        )
        parser.add_argument(
            "--longitude",
            type=float,
            default=-122.084,
            help="Longitude to send in the payload",
        )

    def handle(self, *args, **options):
        channel_name = options["channel"]
        event_name = options["event"]
        rider_id = options["rider"]
        lat = options["latitude"]
        lng = options["longitude"]

        payload = {"rider_id": rider_id, "latitude": lat, "longitude": lng}
        self.stdout.write("Payload to publish:")
        self.stdout.write(json.dumps(payload, indent=2))

        # Publish to Ably
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
            await channel.publish(event_name, payload)

        try:
            asyncio.run(_publish())
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully published location update for rider {rider_id} to channel '{channel_name}' "
                    f"(event: '{event_name}')."
                )
            )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Ably publish failed: {exc}"))
            raise
