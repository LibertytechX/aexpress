import asyncio
import json
import signal as _signal

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Subscribe to a specific user's chat message channel via Ably "
        "and print incoming messages. Press Ctrl+C to stop."
    )

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=str, help="UUID or ID of the user")
        parser.add_argument(
            "--type",
            type=str,
            default="customers",
            choices=["customers", "riders"],
            help="Type of conversation (customers or riders, default: customers)",
        )
        parser.add_argument(
            "--event",
            type=str,
            default="new_message",
            help="Ably event name to filter (default: new_message, use '*' for all events)",
        )

    def handle(self, *args, **options):
        user_id = options["user_id"]
        convo_type = options["type"]
        event_name = options["event"]

        # Note: the model's ably_channel_name property defines the format.
        # Format: f"chat:{convo_type}:{user_id}"
        channel_name = f"chat:{convo_type}:{user_id}"

        api_key = getattr(settings, "ABLY_API_KEY", "")
        if not api_key:
            self.stdout.write(
                self.style.ERROR("ABLY_API_KEY is not configured in settings.")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Subscribing to chat channel: {channel_name} (event: '{event_name}') …"
            )
        )
        self.stdout.write("Press Ctrl+C to stop.\n")

        try:
            asyncio.run(self._listen(api_key, channel_name, event_name))
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\nStopped subscription."))

    async def _listen(self, api_key, channel_name, event_name):
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
                    self.stdout.write(json.dumps(data, indent=2, default=str))
                except Exception:
                    self.stdout.write(str(message.data))
                self.stdout.write("-" * 30)

            # Subscribe to the specific event (or all if event_name == '*')
            if event_name == "*":
                await channel.subscribe(on_message)
            else:
                await channel.subscribe(event_name, on_message)

            self.stdout.write("Connected. Waiting for messages …\n")

            # Run forever until Ctrl+C
            stop_event = asyncio.Event()

            # Signal handler for graceful stop (Mac/Linux)
            def _handle_sigint():
                stop_event.set()

            try:
                loop = asyncio.get_running_loop()
                loop.add_signal_handler(_signal.SIGINT, _handle_sigint)
            except (NotImplementedError, RuntimeError):
                # signal handlers or get_running_loop not available in all contexts
                pass

            await stop_event.wait()
            self.stdout.write(
                self.style.WARNING(
                    f"\nClosing connection. Total received: {received_count}."
                )
            )
