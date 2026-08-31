from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from authentication.models import User
from dispatcher.models import Rider
from riders.models import RiderLocation


class RiderLocationUpdateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone="9876543210",
            email="locationrider@example.com",
            password="password123",
            first_name="Location",
            last_name="Rider",
            business_name="Location Rider Business",
            contact_name="Location Rider Contact",
        )
        self.rider = Rider.objects.create(user=self.user, status="online")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("riders:rider-location-update")

    def test_location_update_creates_record(self):
        """First ping creates a RiderLocation row."""
        data = {
            "latitude": "6.4567890",
            "longitude": "3.1234560",
            "accuracy": 5.0,
            "heading": 90.0,
            "speed": 10.5,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # One record created
        self.assertEqual(RiderLocation.objects.filter(rider=self.rider).count(), 1)
        loc = RiderLocation.objects.get(rider=self.rider)
        self.assertAlmostEqual(float(loc.latitude), 6.4567890, places=6)
        self.assertAlmostEqual(float(loc.longitude), 3.1234560, places=6)
        self.assertEqual(loc.accuracy, 5.0)
        self.assertEqual(loc.heading, 90.0)

        # Also mirrored on the Rider profile
        self.rider.refresh_from_db()
        self.assertAlmostEqual(float(self.rider.current_latitude), 6.4567890, places=6)
        self.assertAlmostEqual(float(self.rider.current_longitude), 3.1234560, places=6)
        self.assertIsNotNone(self.rider.last_location_update)

    def test_second_ping_updates_same_record(self):
        """Subsequent pings update the existing row — no duplicates."""
        self.client.post(
            self.url,
            {"latitude": "6.4567890", "longitude": "3.1234560"},
            format="json",
        )
        self.client.post(
            self.url,
            {"latitude": "6.5000000", "longitude": "3.2000000"},
            format="json",
        )
        # Still only one row
        self.assertEqual(RiderLocation.objects.filter(rider=self.rider).count(), 1)
        loc = RiderLocation.objects.get(rider=self.rider)
        self.assertAlmostEqual(float(loc.latitude), 6.5000000, places=6)
        self.assertAlmostEqual(float(loc.longitude), 3.2000000, places=6)

    def test_missing_required_fields_returns_400(self):
        """Missing latitude / longitude should return 400."""
        response = self.client.post(self.url, {"accuracy": 3.0}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("errors", response.data)

    def test_optional_fields_can_be_omitted(self):
        """Accuracy, heading, speed are optional."""
        data = {"latitude": "6.4567890", "longitude": "3.1234560"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        loc = RiderLocation.objects.get(rider=self.rider)
        self.assertIsNone(loc.accuracy)
        self.assertIsNone(loc.heading)
        self.assertIsNone(loc.speed)
