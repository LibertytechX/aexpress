import os, django, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

import asyncio
from chats.views import _publish_to_ably

def main():
    try:
        _publish_to_ably("chat:test", "new_message", {"test": "data"})
        print("SUCCESS")
    except Exception as e:
        print("FAILED", getattr(e, 'message', str(e)))

main()
