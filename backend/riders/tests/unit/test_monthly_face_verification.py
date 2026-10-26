from datetime import timedelta
from io import StringIO
from unittest.mock import patch, MagicMock
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from authentication.models import User
from dispatcher.models import Rider
from riders.serializers import RiderMeSerializer
from riders.tasks import trigger_monthly_face_verification_task


class MonthlyFaceVerificationTaskTests(TestCase):
    def setUp(self):
        self.now = timezone.now()

        # Helper to create rider
        def create_rider(phone, email, rider_id, is_independent, last_verified, days_created, face_req=False):
            user = User.objects.create_user(
                phone=phone,
                email=email,
                password="testpassword123",
                first_name="Test",
                last_name="Rider",
                usertype="Rider",
            )
            # Rider record created by post_save signal
            rider = user.rider_profile
            rider.rider_id = rider_id
            rider.is_independent_rider = is_independent
            rider.is_authorized = True
            rider.is_active = True
            rider.is_deleted = False
            rider.face_verification_required = face_req
            rider.last_face_verified_at = last_verified
            rider.save()

            # Artificially set created_at via update
            Rider.objects.filter(id=rider.id).update(
                created_at=self.now - timedelta(days=days_created)
            )
            rider.refresh_from_db()
            return rider

        # 1. Independent rider due: verified 35 days ago
        self.rider_due_verified = create_rider(
            phone="08011110001",
            email="due1@example.com",
            rider_id="RD0001",
            is_independent=True,
            last_verified=self.now - timedelta(days=35),
            days_created=60,
        )

        # 2. Independent rider due: never verified, registered 45 days ago
        self.rider_due_unverified = create_rider(
            phone="08011110002",
            email="due2@example.com",
            rider_id="RD0002",
            is_independent=True,
            last_verified=None,
            days_created=45,
        )

        # 3. Independent rider recently verified: verified 10 days ago
        self.rider_recent = create_rider(
            phone="08011110003",
            email="recent@example.com",
            rider_id="RD0003",
            is_independent=True,
            last_verified=self.now - timedelta(days=10),
            days_created=40,
        )

        # 4. Independent rider newly joined: never verified, registered 5 days ago
        self.rider_new = create_rider(
            phone="08011110004",
            email="new@example.com",
            rider_id="RD0004",
            is_independent=True,
            last_verified=None,
            days_created=5,
        )

        # 5. Non-independent rider: verified 50 days ago (company rider)
        self.rider_company = create_rider(
            phone="08011110005",
            email="company@example.com",
            rider_id="RD0005",
            is_independent=False,
            last_verified=self.now - timedelta(days=50),
            days_created=100,
        )

        # 6. Independent rider already flagged for verification
        self.rider_already_flagged = create_rider(
            phone="08011110006",
            email="flagged@example.com",
            rider_id="RD0006",
            is_independent=True,
            last_verified=self.now - timedelta(days=40),
            days_created=80,
            face_req=True,
        )

    @patch("riders.tasks._publish_to_ably_channel")
    def test_task_flags_due_riders_and_publishes_to_ably(self, mock_publish):
        result = trigger_monthly_face_verification_task(days_threshold=30)

        self.assertEqual(result["processed_count"], 2)
        self.assertIn("RD0001", result["due_riders"])
        self.assertIn("RD0002", result["due_riders"])
        self.assertNotIn("RD0003", result["due_riders"])
        self.assertNotIn("RD0004", result["due_riders"])
        self.assertNotIn("RD0005", result["due_riders"])
        self.assertNotIn("RD0006", result["due_riders"])

        # Check DB updates for due rider
        self.rider_due_verified.refresh_from_db()
        self.assertTrue(self.rider_due_verified.face_verification_required)
        self.assertFalse(self.rider_due_verified.is_authorized)

        self.rider_due_unverified.refresh_from_db()
        self.assertTrue(self.rider_due_unverified.face_verification_required)
        self.assertFalse(self.rider_due_unverified.is_authorized)

        # Check Ably publishing
        self.assertEqual(mock_publish.call_count, 2)
        called_channels = [call[0][0] for call in mock_publish.call_args_list]
        self.assertIn("facematch:RD0001", called_channels)
        self.assertIn("facematch:RD0002", called_channels)

        # Verify event and payload structure
        first_call = mock_publish.call_args_list[0]
        channel, event, payload = first_call[0]
        self.assertEqual(event, "facematch_required")
        self.assertEqual(payload["action"], "face_verification_required")
        self.assertEqual(payload["reason"], "monthly_verification")
        self.assertIn("rider_id", payload)
        self.assertIn("due_date", payload)

    @patch("riders.tasks._publish_to_ably_channel")
    def test_task_target_specific_rider(self, mock_publish):
        result = trigger_monthly_face_verification_task(rider_id="RD0001")

        self.assertEqual(result["processed_count"], 1)
        self.assertEqual(result["due_riders"], ["RD0001"])

        self.rider_due_verified.refresh_from_db()
        self.assertTrue(self.rider_due_verified.face_verification_required)
        self.assertFalse(self.rider_due_verified.is_authorized)

        mock_publish.assert_called_once()
        channel, event, payload = mock_publish.call_args[0]
        self.assertEqual(channel, "facematch:RD0001")
        self.assertEqual(event, "facematch_required")


class RiderSerializerAndLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone="08022220001",
            email="rider.login@example.com",
            password="testpassword123",
            first_name="John",
            last_name="Doe",
            usertype="Rider",
        )
        self.rider = self.user.rider_profile
        self.rider.rider_id = "RD8888"
        self.rider.is_independent_rider = True
        self.rider.is_authorized = True
        self.rider.face_verification_required = False
        self.rider.save()

    def test_rider_me_serializer_independent_rider(self):
        serializer = RiderMeSerializer(self.rider)
        data = serializer.data

        self.assertEqual(data["face_verification_channel"], "facematch:RD8888")
        self.assertFalse(data["face_verification_required"])
        self.assertIsNone(data["last_face_verified_at"])
        self.assertTrue(data["is_verified"])

    def test_rider_me_serializer_when_face_verification_required(self):
        self.rider.face_verification_required = True
        self.rider.save()

        serializer = RiderMeSerializer(self.rider)
        data = serializer.data

        self.assertTrue(data["face_verification_required"])
        self.assertFalse(data["is_verified"])

    def test_rider_me_serializer_non_independent_rider(self):
        self.rider.is_independent_rider = False
        self.rider.save()

        serializer = RiderMeSerializer(self.rider)
        data = serializer.data

        self.assertIsNone(data["face_verification_channel"])
        self.assertFalse(data["face_verification_required"])

    def test_rider_login_view_returns_face_verification_channel(self):
        url = reverse("riders:rider-login")
        payload = {
            "phone": "08022220001",
            "password": "testpassword123",
            "device_id": "test_device_1",
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, 200)
        res_data = response.json()

        self.assertTrue(res_data["success"])
        self.assertEqual(res_data["face_verification_channel"], "facematch:RD8888")
        self.assertIn("channels", res_data)
        self.assertEqual(
            res_data["channels"]["face_verification"], "facematch:RD8888"
        )
        self.assertEqual(
            res_data["rider"]["face_verification_channel"], "facematch:RD8888"
        )


class ManagementCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="08033330001",
            email="cmd.rider@example.com",
            password="testpassword123",
            first_name="Cmd",
            last_name="Rider",
            usertype="Rider",
        )
        self.rider = self.user.rider_profile
        self.rider.rider_id = "RD7777"
        self.rider.is_independent_rider = True
        self.rider.is_authorized = True
        self.rider.face_verification_required = False
        self.rider.last_face_verified_at = timezone.now() - timedelta(days=40)
        self.rider.save()

    @patch("riders.tasks._publish_to_ably_channel")
    def test_dry_run_does_not_mutate_or_publish(self, mock_publish):
        out = StringIO()
        call_command("trigger_monthly_face_verification", "--dry-run", stdout=out)

        output = out.getvalue()
        self.assertIn("[DRY-RUN]", output)
        self.assertIn("RD7777", output)

        # DB must NOT be modified
        self.rider.refresh_from_db()
        self.assertFalse(self.rider.face_verification_required)
        self.assertTrue(self.rider.is_authorized)

        # Ably must NOT be published
        mock_publish.assert_not_called()

    @patch("riders.tasks._publish_to_ably_channel")
    def test_command_execution_mutates_and_publishes(self, mock_publish):
        out = StringIO()
        call_command(
            "trigger_monthly_face_verification",
            "--days=30",
            "--rider-id=RD7777",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("Successfully triggered face verification", output)
        self.assertIn("RD7777", output)

        self.rider.refresh_from_db()
        self.assertTrue(self.rider.face_verification_required)
        self.assertFalse(self.rider.is_authorized)

        mock_publish.assert_called_once()
