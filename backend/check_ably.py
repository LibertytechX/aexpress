import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()


def check_ably():
    api_key = getattr(settings, "ABLY_API_KEY", "")
    if not api_key:
        print("ABLY_API_KEY is not configured in settings.")
        return

    import asyncio
    from ably import AblyRest

    print(f"Ably API Key found: {api_key[:5]}...{api_key[-5:]}")

    async def _test_publish():
        try:
            client = AblyRest(api_key)
            channel = client.channels.get("dispatch-feed")
            await channel.publish("test-event", {"message": "testing ably client"})
            print("Successfully published test event to Ably channel 'dispatch-feed'.")
        except Exception as e:
            print(f"Failed to publish to Ably: {e}")

    asyncio.run(_test_publish())


if __name__ == "__main__":
    check_ably()
