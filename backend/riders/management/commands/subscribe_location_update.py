import asyncio
import json
import signal as _signal

from django.conf import settings
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from riders.models import RiderLocation
from dispatcher.models import Rider


class Command(BaseCommand):
    help = (
        "Subscribe to the Ably 'location-update' channel and receive location updates. "
        "Press Ctrl+C to stop."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--channel",
            type=str,
            default="location-update",
            help="Ably channel name to subscribe to (default: location-update)",
        )
        parser.add_argument(
            "--event",
            type=str,
            default="location-update",
            help="Ably event name to filter (default: location-update)",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=0,
            help="Stop automatically after N seconds (0 = run forever until Ctrl+C)",
        )

    def handle(self, *args, **options):
        channel_name = options["channel"]
        event_name = options["event"]
        timeout = options["timeout"]

        api_key = getattr(settings, "ABLY_API_KEY", "")
        if not api_key:
            self.stdout.write(
                self.style.ERROR("ABLY_API_KEY is not configured in settings.")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Subscribing to channel '{channel_name}' (event: '{event_name}') …"
            )
        )
        if timeout:
            self.stdout.write(f"Will auto-stop after {timeout} seconds.")
        self.stdout.write("Press Ctrl+C to stop.\n")
        self.stdout.flush()

        asyncio.run(self._listen(api_key, channel_name, event_name, timeout))

    async def _listen(self, api_key, channel_name, event_name, timeout):
        from ably import AblyRealtime

        received_count = 0

        async with AblyRealtime(api_key) as client:
            channel = client.channels.get(channel_name)

            async def on_message(message):
                nonlocal received_count
                received_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n[#{received_count}] New message received — event: '{message.name}'"
                    )
                )

                try:
                    data = message.data
                    if isinstance(data, str):
                        data = json.loads(data)

                    # Extract payload fields as per the request
                    rider_id = data.get("rider_id", "")
                    latitude = data.get("latitude", "")
                    longitude = data.get("longitude", "")

                    if rider_id and latitude is not None and longitude is not None:
                        # Find the rider and update their location
                        await sync_to_async(self._update_rider_location)(
                            rider_id, latitude, longitude
                        )
                        self.stdout.write(
                            f"Rider ID: {rider_id}, Latitude: {latitude}, Longitude: {longitude}"
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING("Incomplete payload received.")
                        )

                    self.stdout.write(json.dumps(data, indent=2, default=str))
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error processing payload: {e}")
                    )
                    self.stdout.write(str(message.data))
                self.stdout.write("")  # blank line separator
                self.stdout.flush()

            if event_name == "*":
                await channel.subscribe(on_message)
            else:
                await channel.subscribe(event_name, on_message)

            self.stdout.write("Connected. Waiting for messages …\n")
            self.stdout.flush()

            try:
                if timeout:
                    await asyncio.sleep(timeout)
                    self.stdout.write(
                        self.style.WARNING(
                            f"\nTimeout reached ({timeout}s). Received {received_count} message(s)."
                        )
                    )
                else:
                    stop_event = asyncio.Event()

                    def _handle_sigint():
                        stop_event.set()

                    loop = asyncio.get_running_loop()
                    loop.add_signal_handler(_signal.SIGINT, _handle_sigint)
                    loop.add_signal_handler(_signal.SIGTERM, _handle_sigint)

                    await stop_event.wait()
                    self.stdout.write(
                        self.style.WARNING(
                            f"\nStopped by user. Received {received_count} message(s)."
                        )
                    )
            except asyncio.CancelledError:
                pass

    def _update_rider_location(self, rider_id, latitude, longitude):
        try:
            rider = Rider.objects.get(rider_id=rider_id)
            RiderLocation.objects.update_or_create(
                rider=rider, defaults={"latitude": latitude, "longitude": longitude}
            )

            # Update the Rider model itself
            rider.current_latitude = latitude
            rider.current_longitude = longitude
            rider.save(update_fields=["current_latitude", "current_longitude"])

        except Rider.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Rider with ID {rider_id} does not exist.")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to update location for {rider_id}: {e}")
            )
