import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from riders.models import RiderNotification, RiderDevice
from riders.notifications import notify_rider
from dispatcher.models import Rider
from authentication.models import User


def test_notifications():
    # 1. Get or create a test rider
    user = User.objects.filter(phone="1234567890").first()
    if not user:
        user = User.objects.create_user(
            phone="1234567890",
            email="test@example.com",
            password="password",
            business_name="Test Biz",
            contact_name="Test Contact",
        )

    rider = Rider.objects.filter(user=user).first()
    if not rider:
        rider = Rider.objects.create(user=user, rider_id="TEST01")

    # 2. Add a dummy device with a fake token
    device, _ = RiderDevice.objects.update_or_create(
        device_id="test-device-uuid",
        defaults={"rider": rider, "fcm_token": "fake-fcm-token", "is_active": True},
    )

    print(f"Testing notification for Rider: {rider.rider_id}")

    # 3. Call notify_rider
    title = "Test Notification"
    body = "This is a test notification from Antigravity"
    data = {"order_id": "12345"}

    notify_rider(rider, title, body, data)

    # 4. Verify persistence
    notification = RiderNotification.objects.filter(rider=rider, title=title).first()
    if notification:
        print(f"SUCCESS: Notification persisted in DB with ID {notification.id}")
    else:
        print("FAILURE: Notification not found in DB")


if __name__ == "__main__":
    test_notifications()
