import os
import django
import sys

# Setup Django environment
sys.path.append("/Users/ayo/Liberty/aexpress/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")

try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from authentication.models import User
from dispatcher.models import Rider, Vehicle
from rest_framework.test import APIRequestFactory, force_authenticate
from dispatcher.views import RiderViewSet


def verify_rider_flow():
    print("Verifying Rider Flow...")

    # 1. Create User with type 'Rider'
    phone = "+2348000000001"
    email = "rider.test@example.com"
    try:
        user = User.objects.get(phone=phone)
        print(f"User {phone} already exists. Deleting...")
        user.delete()
    except User.DoesNotExist:
        pass

    print(f"Creating user {phone} with usertype='Rider'...")
    try:
        user = User.objects.create_user(
            phone=phone,
            email=email,
            password="password123",
            usertype="Rider",
            contact_name="Test Rider",
            business_name="Rider Business",  # Optional now, but providing for test
        )
    except Exception as e:
        print(f"Error creating user: {e}")
        return

    # 2. Check if Rider profile exists (Signal verification)
    try:
        rider = Rider.objects.get(user=user)
        print("SUCCESS: Rider profile created automatically via signal.")
    except Rider.DoesNotExist:
        print("FAILURE: Rider profile NOT created.")
        return

    # 3. Create a Vehicle and assign
    print("Creating Vehicle...")
    try:
        vehicle = Vehicle.objects.create(
            type="Bike", plate_number="LAG-123-KD", model="Yamaha 2020", color="Red"
        )
        rider.vehicle = vehicle
        rider.save()
        print("Vehicle assigned to Rider.")
    except Exception as e:
        print(f"Error creating vehicle: {e}")

    # 4. Test API Endpoint (using ViewSet directly / RequestFactory)
    print("Testing API ViewSet...")
    factory = APIRequestFactory()
    view = RiderViewSet.as_view({"get": "list"})

    request = factory.get("/api/dispatch/riders/")
    force_authenticate(request, user=user)

    response = view(request)
    print(f"API Response Code: {response.status_code}")

    if response.status_code == 200:
        data = response.data
        if len(data) > 0:
            # Check if our rider is in the list
            found = False
            for r in data:
                if r["phone"] == phone:
                    found = True
                    print(f"Found Rider: {r['name']}, Vehicle: {r['vehicle']}")
                    if r["vehicle"] == "Bike":
                        print("SUCCESS: Vehicle type mapping correct.")
                    else:
                        print(
                            f"FAILURE: Vehicle type mismatch. Expected 'Bike', got '{r['vehicle']}'"
                        )
            if not found:
                print("FAILURE: Created rider not found in list.")
        else:
            print("FAILURE: API returned empty list.")
    else:
        print(f"FAILURE: API failed with {response.status_code}")

    # Cleanup
    print("Cleaning up...")
    user.delete()
    vehicle.delete()


if __name__ == "__main__":
    verify_rider_flow()
