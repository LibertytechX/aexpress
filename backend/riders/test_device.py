from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from dispatcher.models import Rider
from authentication.models import User
from riders.models import RiderDevice
import uuid


class RiderDeviceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Custom User model uses phone as identifier and requires email, business_name, contact_name
        self.user = User.objects.create_user(
            phone="1234567890",
            email="testrider@example.com",
            password="password123",
            first_name="Test",
            last_name="Rider",
            business_name="Test Rider Business",
            contact_name="Test Rider Contact",
        )
        self.rider = Rider.objects.create(user=self.user, status="online")
        self.client.force_authenticate(user=self.user)

    def test_register_device(self):
        url = reverse("riders:rider-device-register")
        data = {
            "device_id": "test-device-123",
            "fcm_token": "test-fcm-token",
            "platform": "ios",
            "model_name": "iPhone 13",
            "os_version": "15.0",
            "app_version": "1.0.0",
            "location_permission": "granted",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

        # Verify in DB
        device = RiderDevice.objects.get(device_id="test-device-123")
        self.assertEqual(device.rider, self.rider)
        self.assertEqual(device.platform, "ios")
        self.assertEqual(device.location_permission, "granted")

    def test_update_permissions(self):
        # First register a device
        device = RiderDevice.objects.create(
            rider=self.rider, device_id="test-device-123", is_active=True
        )

        url = reverse("riders:rider-device-permissions")
        data = {"camera_permission": "granted", "notification_permission": "denied"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # Verify in DB
        device.refresh_from_db()
        self.assertEqual(device.camera_permission, "granted")
        self.assertEqual(device.notification_permission, "denied")
