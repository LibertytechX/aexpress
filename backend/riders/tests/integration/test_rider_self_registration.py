from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from dispatcher.models import Rider
from dispatcher.serializers import RiderApprovalSerializer
from riders.models import RiderDocument, RiderSession


class RiderSelfRegistrationIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("riders:rider-register")
        self.payload = {
            "phone": "08123456789",
            "email": "selfreg.rider@test.com",
            "first_name": "Tunde",
            "last_name": "Bakare",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "address": "45 Broad St, Lagos Island",
            "emergency_contact_name": "Funke Bakare",
            "emergency_phone": "08033344455",
            "bvn": "22334455667",
            "vehicle_model": "Bajaj Boxer 150",
            "vehicle_plate_number": "EKY-456-AA",
            "vehicle_color": "Blue",
            "vehicle_photo": "https://storage.aexpress.com/vehicles/bajaj.jpg",
            "device_id": "device-uuid-999",
            "device_name": "Samsung Galaxy A53",
            "device_os": "android",
            "fcm_token": "fcm-token-xyz-123",
            "rider_documents": [
                {
                    "type": RiderDocument.DocType.NATIONAL_ID,
                    "url": "https://storage.aexpress.com/docs/nin.jpg",
                },
                {
                    "type": RiderDocument.DocType.RIDERS_CARD,
                    "url": "https://storage.aexpress.com/docs/rcard.jpg",
                },
                {
                    "type": RiderDocument.DocType.DRIVERS_LICENSE,
                    "url": "https://storage.aexpress.com/docs/license.jpg",
                },
                {
                    "type": RiderDocument.DocType.UTILITY_BILL,
                    "url": "https://storage.aexpress.com/docs/bill.jpg",
                },
                {
                    "type": RiderDocument.DocType.PROFILE_PHOTO,
                    "url": "https://storage.aexpress.com/docs/profile.jpg",
                },
            ],
        }

    def test_self_registration_endpoint_success(self):
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get("success"))
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

        rider_data = response.data.get("rider", {})
        self.assertEqual(rider_data.get("emergency_contact_name"), "Funke Bakare")
        self.assertEqual(rider_data.get("emergency_phone"), "+2348033344455")

        # Verify Database records
        rider = Rider.objects.get(user__phone="+2348123456789")
        self.assertEqual(rider.emergency_contact_name, "Funke Bakare")
        self.assertEqual(rider.emergency_phone, "+2348033344455")
        self.assertEqual(rider.approval_status, Rider.ApprovalStatus.PENDING)
        self.assertFalse(rider.is_authorized)
        self.assertTrue(rider.is_independent_rider)

        # Verify session created
        session = RiderSession.objects.filter(rider=rider).first()
        self.assertIsNotNone(session)
        self.assertEqual(session.device_id, "device-uuid-999")

        # Verify RiderApprovalSerializer for ops review
        approval_data = RiderApprovalSerializer(rider).data
        self.assertEqual(approval_data["emergency_contact_name"], "Funke Bakare")
        self.assertEqual(approval_data["emergency_phone"], "+2348033344455")

    def test_self_registration_missing_emergency_details_fails(self):
        payload = self.payload.copy()
        payload.pop("emergency_contact_name")
        payload.pop("emergency_phone")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get("success"))
        self.assertIn("emergency_contact_name", response.data.get("errors", {}))
        self.assertIn("emergency_phone", response.data.get("errors", {}))

