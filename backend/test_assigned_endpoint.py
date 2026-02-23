import os
import django
import sys

# Setup django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from authentication.models import User
from dispatcher.models import Rider
from orders.models import Order, Delivery, Vehicle
from orders.serializers import AssignedOrderSerializer
from django.utils import timezone
from decimal import Decimal


def test_endpoint():
    print("Setting up test data...")
    try:
        # Get or create rider user
        user, _ = User.objects.get_or_create(
            email="rider_test@example.com",
            defaults={
                "first_name": "Test",
                "last_name": "Rider",
                "role": "rider",
                "business_name": "Test Rider",
            },
        )
        # Get or create rider profile
        rider, _ = Rider.objects.get_or_create(
            user=user, defaults={"phone_number": "08012345678", "status": "online"}
        )

        # Get or create a merchant user
        merchant, _ = User.objects.get_or_create(
            email="merchant_test@example.com",
            defaults={
                "first_name": "QuickMart",
                "last_name": "Supermarket",
                "role": "merchant",
                "business_name": "QuickMart",
            },
        )

        # Get or create a vehicle
        vehicle, _ = Vehicle.objects.get_or_create(
            name="bike",
            defaults={"max_weight_kg": 50, "base_price": 500, "base_fare": 500},
        )

        # Create an order
        order = Order.objects.create(
            user=merchant,
            rider=rider,
            vehicle=vehicle,
            pickup_address="78 Allen Avenue, Ikeja, Lagos",
            pickup_latitude=6.6018,
            pickup_longitude=3.3515,
            sender_name="QuickMart Supermarket",
            sender_phone="+2348045678901",
            notes="Use back entrance for pickups",
            payment_method="cash_on_pickup",
            total_amount=Decimal("800.00"),
            distance_km=Decimal("2.8"),
            duration_minutes=12,
            status="Assigned",
        )

        # Create a delivery
        delivery = Delivery.objects.create(
            order=order,
            dropoff_address="23 Opebi Road, Ikeja, Lagos",
            dropoff_latitude=6.5955,
            dropoff_longitude=3.3565,
            receiver_name="Mr. Ibrahim",
            receiver_phone="+2348056789012",
            notes="Leave at security post if not available",
            cod_amount=Decimal("15500.00"),
            cod_from="customer",
        )

        # Serialize
        serializer = AssignedOrderSerializer(order)
        import json

        print("====== SERIALIZED DATA ======")
        print(json.dumps(serializer.data, indent=2))
        print("=============================")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_endpoint()
