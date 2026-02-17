import os
import django
import sys
import random
import string

# Setup Django environment
sys.path.append("/Users/ayo/Liberty/aexpress/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")

try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from authentication.models import User
from dispatcher.models import Rider
from orders.models import Vehicle as OrderVehicle
from orders.models import Order
from rest_framework.test import APIRequestFactory, force_authenticate
from dispatcher.views import RiderViewSet


def verify_refactored_flow():
    print("Verifying Refactored Rider Flow...")

    # 1. Create User with type 'Rider'
    phone = "+234899999999"
    email = "rider_refactor@example.com"
    try:
        if User.objects.filter(phone=phone).exists():
            User.objects.filter(phone=phone).delete()
    except Exception:
        pass

    print(f"Creating user {phone}...")
    user = User.objects.create_user(
        phone=phone,
        email=email,
        password="password123",
        usertype="Rider",
        contact_name="Refactored Rider",
        business_name="Rider Biz",
    )

    # 2. Check Rider profile and ID
    try:
        rider = Rider.objects.get(user=user)
        print(f"SUCCESS: Rider profile created. ID: {rider.rider_id}")
        if len(rider.rider_id) == 6:
            print("SUCCESS: Rider ID length is 6.")
        else:
            print(f"FAILURE: Rider ID length is {len(rider.rider_id)}, expected 6.")
    except Rider.DoesNotExist:
        print("FAILURE: Rider profile NOT created.")
        return

    # 3. Create Order Vehicle (Type) and Assign
    print("Creating/Getting Vehicle Type (orders.Vehicle)...")
    vehicle_type, _ = OrderVehicle.objects.get_or_create(
        name="TestBike", defaults={"max_weight_kg": 50, "base_price": 1000}
    )

    rider.vehicle_type = vehicle_type
    rider.plate_number = "LAG-555-ZZ"
    rider.model = "Honda Ace"
    rider.color = "Black"
    rider.save()
    print("Vehicle details assigned to Rider.")

    # 4. Create Order and Assign Rider
    print("Creating Order and assigning Rider...")
    try:
        # Create a merchant user for the order
        merchant = User.objects.create_user(
            phone="+234888888888", email="merchant@test.com", password="pass"
        )

        order = Order.objects.create(
            user=merchant,
            pickup_address="A",
            sender_name="S",
            sender_phone="1",
            total_amount=100,
            vehicle=vehicle_type,
            rider=rider,  # Testing the new FK
        )
        print(f"SUCCESS: Order created with rider assigned: {order.rider}")
    except Exception as e:
        print(f"FAILURE: Could not create order with rider: {e}")
        merchant.delete()
        user.delete()
        return

    # 5. Test API Endpoint
    print("Testing API ViewSet...")
    factory = APIRequestFactory()
    view = RiderViewSet.as_view({"get": "list"})

    request = factory.get("/api/dispatch/riders/")
    force_authenticate(request, user=user)

    response = view(request)

    print(f"API Response Code: {response.status_code}")
    if response.status_code == 200:
        data = response.data
        found = False
        for r in data:
            if r["rider_id"] == rider.rider_id:
                found = True
                print(f"Found Rider via API: {r['rider_id']}")
                print(f"Vehicle: {r['vehicle']}, Plate: {r['plate_number']}")
                if r["vehicle"] == "TestBike" and r["plate_number"] == "LAG-555-ZZ":
                    print("SUCCESS: API returns correct refactored fields.")
                else:
                    print("FAILURE: API data mismatch.")
        if not found:
            print("FAILURE: Created rider not found in API response.")
    else:
        print(f"FAILURE: API failed with {response.status_code}")

    # Cleanup
    print("Cleaning up...")
    order.delete()
    merchant.delete()
    user.delete()


if __name__ == "__main__":
    verify_refactored_flow()
