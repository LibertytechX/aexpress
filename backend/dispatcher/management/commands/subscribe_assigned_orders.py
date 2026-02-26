import asyncio
import json
import signal as _signal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Subscribe to an Ably 'assigned-{rider_id}' channel and print every "
        "incoming order_assigned event. Usage: python manage.py subscribe_assigned_orders <rider_id>"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "rider_id",
            type=str,
            help="Rider ID whose assignment channel to watch (e.g. RID-001)",
        )
        parser.add_argument(
            "--event",
            type=str,
            default="order_assigned",
            help="Ably event name to filter (default: order_assigned, use '*' for all)",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=0,
            help="Stop automatically after N seconds (0 = run forever until Ctrl+C)",
        )

    def handle(self, *args, **options):
        rider_id = options["rider_id"]
        event_name = options["event"]
        timeout = options["timeout"]

        # Validate rider exists
        from dispatcher.models import Rider

        try:
            rider = Rider.objects.get(rider_id=rider_id)
        except Rider.DoesNotExist:
            raise CommandError(f"Rider '{rider_id}' not found.")

        api_key = getattr(settings, "ABLY_API_KEY", "")
        if not api_key:
            self.stdout.write(
                self.style.ERROR("ABLY_API_KEY is not configured in settings.")
            )
            return

        channel_name = f"order"
        rider_name = (
            getattr(rider.user, "get_full_name", lambda: rider_id)() or rider_id
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Subscribing to channel '{channel_name}' (event: '{event_name}') "
                f"for rider {rider_name} …"
            )
        )
        if timeout:
            self.stdout.write(f"Will auto-stop after {timeout} seconds.")
        self.stdout.write("Press Ctrl+C to stop.\n")

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
                        f"\n[#{received_count}] Order assigned — event: '{message.name}'"
                    )
                )
                try:
                    data = message.data
                    if isinstance(data, str):
                        data = json.loads(data)
                    self.stdout.write(json.dumps(data, indent=2, default=str))
                except Exception:
                    self.stdout.write(str(message.data))
                self.stdout.write("")  # blank line separator

            if event_name == "*":
                await channel.subscribe(on_message)
            else:
                await channel.subscribe(event_name, on_message)

            self.stdout.write("Connected. Waiting for assignments …\n")

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

                    await stop_event.wait()
                    self.stdout.write(
                        self.style.WARNING(
                            f"\nStopped by user. Received {received_count} message(s)."
                        )
                    )
            except asyncio.CancelledError:
                pass
