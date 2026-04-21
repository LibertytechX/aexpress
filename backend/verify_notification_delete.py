import os
import django
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from authentication.models import User
from dispatcher.models import Merchant, MerchantNotification
from rest_framework.test import APIRequestFactory, force_authenticate
from authentication.views import MerchantNotificationDeleteView, MerchantNotificationDeleteAllView
from django.shortcuts import get_object_or_404

def verify():
    # 1. Setup test data
    phone = "09000000000"
    user, created = User.objects.get_or_create(
        phone=phone,
        defaults={
            "email": "merchant@test.com",
            "business_name": "Test Merchant",
            "contact_name": "Merchant Contact",
            "user_type": "merchant"
        }
    )
    if created:
        user.set_password("password123")
        user.save()

    merchant, _ = Merchant.objects.get_or_create(user=user)

    # Clear existing notifications for clean test
    MerchantNotification.objects.filter(merchant=merchant).delete()

    # Create 3 notifications
    n1 = MerchantNotification.objects.create(merchant=merchant, title="Notif 1", body="Body 1")
    n2 = MerchantNotification.objects.create(merchant=merchant, title="Notif 2", body="Body 2")
    n3 = MerchantNotification.objects.create(merchant=merchant, title="Notif 3", body="Body 3")

    print(f"Created 3 notifications for merchant {merchant.merchant_id}")

    factory = APIRequestFactory()

    # 2. Test Single Delete
    print(f"Testing single delete for notification ID: {n1.id}")
    view = MerchantNotificationDeleteView.as_view()
    request = factory.delete(f'/api/auth/notifications/{n1.id}/')
    force_authenticate(request, user=user)
    response = view(request, pk=n1.id)

    print(f"Delete single response: {response.status_code} - {response.data}")
    assert response.status_code == 200
    assert not MerchantNotification.objects.filter(id=n1.id).exists()
    print("SUCCESS: Single notification deleted.")

    # 3. Test Delete All
    print("Testing delete all notifications")
    view_all = MerchantNotificationDeleteAllView.as_view()
    request_all = factory.delete('/api/auth/notifications/delete-all/')
    force_authenticate(request_all, user=user)
    response_all = view_all(request_all)

    print(f"Delete all response: {response_all.status_code} - {response_all.data}")
    assert response_all.status_code == 200
    assert MerchantNotification.objects.filter(merchant=merchant).count() == 0
    print("SUCCESS: All notifications deleted.")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
