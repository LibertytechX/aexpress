import os
import django
import sys
from datetime import timedelta
from django.utils import timezone

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from authentication.models import User
from dispatcher.models import Rider
from riders.models import RiderAuth, RiderSession
from rest_framework.test import APIClient
from django.contrib.auth.hashers import make_password


def setup_test_rider():
    phone = "08012345678"
    password = "password123"
    email = "testrider@example.com"

    # 1. Create User
    user, created = User.objects.get_or_create(
        phone=phone,
        defaults={
            "email": email,
            "business_name": "Test Rider Delivery",
            "contact_name": "Test Rider",
            "usertype": "Rider",
            "is_active": True,
        },
    )
    if not created:
        user.email = email
        user.usertype = "Rider"
        user.is_active = True
        user.save()

    user.set_password(password)
    user.save()

    # 2. Create Rider Profile
    rider, created = Rider.objects.get_or_create(
        user=user,
        defaults={"status": "offline", "is_authorized": True, "is_active": True},
    )
    if not created:
        rider.is_authorized = True
        rider.is_active = True
        rider.save()

    # 3. Create RiderAuth
    auth, created = RiderAuth.objects.get_or_create(
        rider=rider, defaults={"is_active": True, "is_verified": True}
    )
    if not created:
        auth.is_active = True
        auth.is_verified = True
        auth.save()

    # We don't set password in RiderAuth because the serializer uses User authentication
    # but let's set it anyway for completeness since we ported the model
    auth.set_password(password)
    auth.save()

    print(f"Test Rider Created: {phone} / {password}")
    return phone, password


def test_login(phone, password):
    from django.conf import settings

    if "testserver" not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append("testserver")

    client = APIClient()
    url = "/api/riders/auth/login/"
    data = {
        "phone": phone,
        "password": password,
        "device_id": "test-device-uuid",
        "device_name": "Antigravity Tester",
        "device_os": "ios",
        "fcm_token": "test-fcm-token",
    }

    print(f"Testing Login at {url}...")
    response = client.post(url, data, format="json")

    if response.status_code == 200:
        print("✅ Login Successful!")
        print(f"Response: {response.json()}")

        # Verify Session creation
        session_exists = RiderSession.objects.filter(
            device_id="test-device-uuid"
        ).exists()
        if session_exists:
            print("✅ RiderSession correctly created.")
        else:
            print("❌ RiderSession NOT created.")
    else:
        print(f"❌ Login Failed! Status: {response.status_code}")
        try:
            print(f"Error: {response.json()}")
        except Exception:
            print(f"Raw Output: {response.content[:500]}")


if __name__ == "__main__":
    phone, password = setup_test_rider()
    test_login(phone, password)
