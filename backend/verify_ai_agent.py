import os
import json
import asyncio
import django


# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from django.contrib.auth import get_user_model
from chats.ai_engine import get_ai_response

User = get_user_model()


async def test_ai_agent():
    # 1. Ensure we have a test user (Use async aget_or_create for Django 4.2+)
    user, created = await User.objects.aget_or_create(
        phone="08012345678",
        defaults={
            "email": "test_customer@example.com",
            "usertype": "Customer",
            "first_name": "Test",
            "last_name": "User"
        }
    )

    user_id = str(user.id)
    print(f"Testing with User ID: {user_id} ({user.get_full_name()})")

    # 2. Simulate an order-related query
    print("\n--- Test 1: Order Query (Checking Routing + Tool Use) ---")
    user_message = "Where is my order ORD-5678?"
    raw_response = await get_ai_response("some-convo-id", user_id, user_message)

    try:
        response_data = json.loads(raw_response)
        print(f"Category: {response_data.get('category')}")
        print(f"AI: {response_data.get('response')}")
    except (json.JSONDecodeError, TypeError):
        print(f"AI (Raw): {raw_response}")

    # 3. Simulate a technical query
    print("\n--- Test 2: Technical Query (Checking Routing) ---")
    user_message = "I cannot login to the dispatcher portal."
    raw_response = await get_ai_response("some-convo-id", user_id, user_message)

    try:
        response_data = json.loads(raw_response)
        print(f"Category: {response_data.get('category')}")
        print(f"AI: {response_data.get('response')}")
    except (json.JSONDecodeError, TypeError):
        print(f"AI (Raw): {raw_response}")


if __name__ == "__main__":
    asyncio.run(test_ai_agent())
