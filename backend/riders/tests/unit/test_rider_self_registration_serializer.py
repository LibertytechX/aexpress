from django.test import TestCase
from dispatcher.models import Rider
from riders.models import RiderDocument
from riders.serializers import (
    RiderSelfRegistrationSerializer,
    RiderMeSerializer,
)


class RiderSelfRegistrationSerializerTests(TestCase):
    def setUp(self):
        self.valid_data = {
            "phone": "08012345678",
            "email": "rider.test@example.com",
            "first_name": "Ade",
            "last_name": "Babatunde",
            "password": "SecurePassword123",
            "confirm_password": "SecurePassword123",
            "address": "123 Lagos St, Ikeja",
            "emergency_contact_name": "Bola Babatunde",
            "emergency_phone": "08098765432",
            "bvn": "12345678901",
            "vehicle_model": "Honda Ace 125",
            "vehicle_plate_number": "LAG-123-XY",
            "vehicle_color": "Red",
            "vehicle_photo": "https://storage.aexpress.com/vehicles/photo.jpg",
            "rider_documents": [
                {
                    "type": RiderDocument.DocType.NATIONAL_ID,
                    "url": "https://storage.aexpress.com/docs/nin.pdf",
                },
                {
                    "type": RiderDocument.DocType.RIDERS_CARD,
                    "url": "https://storage.aexpress.com/docs/riders_card.pdf",
                },
                {
                    "type": RiderDocument.DocType.DRIVERS_LICENSE,
                    "url": "https://storage.aexpress.com/docs/license.pdf",
                },
                {
                    "type": RiderDocument.DocType.UTILITY_BILL,
                    "url": "https://storage.aexpress.com/docs/bill.pdf",
                },
                {
                    "type": RiderDocument.DocType.PROFILE_PHOTO,
                    "url": "https://storage.aexpress.com/docs/photo.jpg",
                },
            ],
        }

    def test_valid_registration_with_emergency_contact(self):
        serializer = RiderSelfRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()

        user, rider = result["user"], result["rider"]
        self.assertEqual(user.phone, "+2348012345678")
        self.assertEqual(rider.emergency_contact_name, "Bola Babatunde")
        self.assertEqual(rider.emergency_phone, "+2348098765432")
        self.assertEqual(rider.working_type, "freelancer")
        self.assertTrue(rider.is_independent_rider)
        self.assertFalse(rider.is_authorized)
        self.assertEqual(rider.approval_status, Rider.ApprovalStatus.PENDING)

    def test_emergency_contact_phone_validation(self):
        data = self.valid_data.copy()
        data["emergency_phone"] = "invalid-phone"
        serializer = RiderSelfRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("emergency_phone", serializer.errors)

    def test_missing_emergency_contact_name(self):
        data = self.valid_data.copy()
        data.pop("emergency_contact_name")
        serializer = RiderSelfRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("emergency_contact_name", serializer.errors)

    def test_missing_emergency_phone(self):
        data = self.valid_data.copy()
        data.pop("emergency_phone")
        serializer = RiderSelfRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("emergency_phone", serializer.errors)

    def test_rider_me_serializer_includes_emergency_contact(self):
        serializer = RiderSelfRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        result = serializer.save()
        rider = result["rider"]

        me_data = RiderMeSerializer(rider).data
        self.assertEqual(me_data["emergency_contact_name"], "Bola Babatunde")
        self.assertEqual(me_data["emergency_phone"], "+2348098765432")

