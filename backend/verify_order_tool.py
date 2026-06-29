import os
import django
import asyncio
from asgiref.sync import sync_to_async
from orders.models import Order, Vehicle
from authentication.models import User
from chats.ai_engine import check_order_status

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()


@sync_to_async
def setup_data():
    # 1. Get or create a merchant user
    merchant, _ = User.objects.get_or_create(
        phone="+2347000000000",
        defaults={
            "email": "test_merchant@aexpress.com",
            "usertype": "Merchant",
            "contact_name": "Test Merchant",
        },
    )

    # 2. Get or create a vehicle
    vehicle, _ = Vehicle.objects.get_or_create(
        name="Bike",
        defaults={
            "max_weight_kg": 20,
            "base_price": 500,
            "base_fare": 500,
            "rate_per_km": 100,
        },
    )

    # 3. Create a test order
    order = Order.objects.create(
        user=merchant,
        vehicle=vehicle,
        pickup_address="123 Test Street",
        total_amount=1500,
        payment_status="Paid",
        status="Pending",
    )
    return order.order_number


async def test_order_tool():
    order_num = await setup_data()
    print(f"Created Test Order: {order_num}")

    # 4. Test tool with raw ID
    result_raw = await check_order_status(order_num)
    print(f"\nResult (raw ID):")
    print(result_raw)

    # 5. Test tool with ORD- prefix
    result_prefix = await check_order_status(f"ORD-{order_num}")
    print(f"\nResult (ORD- prefix):")
    print(result_prefix)

    # 6. Test with invalid ID
    result_invalid = await check_order_status("ORD-9999999")
    print(f"\nResult (invalid ID):")
    print(result_invalid)

    # Cleanup
    # order.delete() # Optional


if __name__ == "__main__":
    asyncio.run(test_order_tool())
