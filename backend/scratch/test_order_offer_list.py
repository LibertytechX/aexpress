import os
import django
import json
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from rest_framework.test import APIClient
from authentication.models import User
from orders.models import Order, Vehicle, Delivery
from riders.models import OrderOffer
from dispatcher.models import Rider
from django.utils import timezone


def verify_list_endpoint():
    print("--- Verifying OrderOffer List Endpoint ---")

    # 1. Setup Rider User and Authentication
    rider_user = User.objects.filter(usertype="Rider").first()
    if not rider_user:
        print("Creating dummy rider user...")
        rider_user = User.objects.create_user(
            phone="+2348111222333",
            password="password123",
            usertype="Rider",
            first_name="Test",
            last_name="Rider",
        )

    # Ensure rider profile exists
    rider_profile, _ = Rider.objects.get_or_create(user=rider_user)

    client = APIClient()
    client.force_authenticate(user=rider_user)

    # 2. Create a Merchant User and Vehicle (if not exists)
    merchant_user = User.objects.filter(usertype="Merchant").first()
    vehicle = Vehicle.objects.filter(is_active=True).first()

    # 3. Create an Order and trigger the signal
    print("Creating order to trigger OrderOffer creation...")
    order = Order.objects.create(
        user=merchant_user,
        vehicle=vehicle,
        pickup_address="15 Adeola Odeku Street, Victoria Island, Lagos",
        pickup_latitude=6.4281,
        pickup_longitude=3.4219,
        sender_name="The Place",
        total_amount=Decimal("1500.00"),
        payment_method="wallet",
        distance_km=6.5,
        duration_minutes=22,
    )

    # Create a delivery for the order
    Delivery.objects.create(
        order=order,
        dropoff_address="89 Awolowo Road, Ikoyi, Lagos",
        dropoff_latitude=6.4541,
        dropoff_longitude=3.4316,
        receiver_name="Dr. Adeleke",
        receiver_phone="123456789",
        cod_amount=0,
    )

    # 4. Call the endpoint
    print("Calling GET /api/riders/orders/offers/...")
    response = client.get("/api/riders/orders/offers/")

    if response.status_code == 200:
        print("✓ SUCCESS: Endpoint returned 200 OK")
        data = response.data
        if isinstance(data, list) and len(data) > 0:
            print(f"✓ SUCCESS: Returned {len(data)} offers")
            offer = data[0]

            # Check for requested fields
            required_fields = [
                "id",
                "order_id",
                "order_ref",
                "status",
                "estimated_earnings",
                "estimated_distance_km",
                "estimated_eta_mins",
                "pickup_address",
                "dropoff_address",
                "pickup_latitude",
                "pickup_longitude",
                "dropoff_latitude",
                "dropoff_longitude",
                "vehicle_type",
                "payment_method",
                "merchant_name",
                "pickup_contact_name",
                "dropoff_contact_name",
                "cod_amount",
                "seconds_remaining",
                "expires_at",
            ]

            missing = [f for f in required_fields if f not in offer]
            if not missing:
                print("✓ SUCCESS: All requested fields are present in the response")
                print("\nSample Offer Data:")
                print(json.dumps(offer, indent=2))
            else:
                print(f"✗ FAILURE: Missing fields: {missing}")
                print(json.dumps(offer, indent=2))
        else:
            print("✗ FAILURE: No offers returned in list")
    else:
        print(f"✗ FAILURE: Endpoint returned {response.status_code}")
        print(response.data)


if __name__ == "__main__":
    verify_list_endpoint()
