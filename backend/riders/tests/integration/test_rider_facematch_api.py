from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from authentication.models import User
from dispatcher.models import Rider
from riders.models import RiderDocument, RiderFaceMatchLog


class RiderFaceMatchAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Independent Rider User
        self.user = User.objects.create_user(
            phone="08022334455",
            email="independent.rider@example.com",
            password="securepassword123",
            first_name="Independent",
            last_name="Rider",
            contact_name="Independent Rider",
            usertype="Rider",
        )
        self.rider = Rider.objects.create(
            user=self.user,
            rider_id="RD5555",
            is_independent_rider=True,
            is_authorized=True,
            status=Rider.Status.ONLINE,
        )
        self.profile_doc = RiderDocument.objects.create(
            rider=self.rider,
            doc_type=RiderDocument.DocType.PROFILE_PHOTO,
            file_url="https://storage.aexpress.com/docs/ref_profile.jpg",
            status=RiderDocument.Status.APPROVED,
        )

        # Create Company / Non-independent Rider User
        self.company_user = User.objects.create_user(
            phone="08033445566",
            email="company.rider@example.com",
            password="securepassword123",
            first_name="Company",
            last_name="Rider",
            contact_name="Company Rider",
            usertype="Rider",
        )
        self.company_rider = Rider.objects.create(
            user=self.company_user,
            rider_id="RD6666",
            is_independent_rider=False,
            is_authorized=True,
            status=Rider.Status.ONLINE,
        )

        self.url = reverse("riders:rider-facematch")

    @patch("riders.tasks.process_rider_facematch_task.delay")
    def test_facematch_success_returns_202_and_channel(self, mock_task):
        self.client.force_authenticate(user=self.user)
        payload = {"image_url": "https://storage.aexpress.com/selfies/snapshot_123.jpg"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        res_data = response.data
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(res_data["data"]["channel"], f"facematch:{self.rider.rider_id}")
        self.assertEqual(res_data["data"]["event"], "facematch_result")
        self.assertEqual(res_data["data"]["status"], "processing")

        # Celery task dispatched
        mock_task.assert_called_once()
        task_kwargs = mock_task.call_args.kwargs
        self.assertEqual(task_kwargs["rider_id"], str(self.rider.id))
        self.assertEqual(task_kwargs["selfie_url"], payload["image_url"])
        self.assertEqual(task_kwargs["channel_name"], f"facematch:{self.rider.rider_id}")

        # FaceMatch log created with PENDING
        log = RiderFaceMatchLog.objects.filter(rider=self.rider).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, RiderFaceMatchLog.Status.PENDING)
        self.assertEqual(log.selfie_url, payload["image_url"])
        self.assertEqual(log.reference_photo_url, self.profile_doc.file_url)

    def test_facematch_alias_url(self):
        self.client.force_authenticate(user=self.user)
        alias_url = reverse("riders:rider-face-match")
        with patch("riders.tasks.process_rider_facematch_task.delay"):
            response = self.client.post(
                alias_url,
                {"image_url": "https://storage.aexpress.com/selfies/test.jpg"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_facematch_rejects_non_independent_rider(self):
        self.client.force_authenticate(user=self.company_user)
        payload = {"image_url": "https://storage.aexpress.com/selfies/snapshot_123.jpg"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("only applicable to independent riders", response.data.get("message", ""))

    def test_facematch_rejects_when_missing_profile_photo(self):
        # Delete profile photo document
        self.profile_doc.delete()
        self.client.force_authenticate(user=self.user)
        payload = {"image_url": "https://storage.aexpress.com/selfies/snapshot_123.jpg"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No reference profile photo found", response.data.get("message", ""))

    def test_facematch_unauthenticated_request(self):
        payload = {"image_url": "https://storage.aexpress.com/selfies/snapshot_123.jpg"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_facematch_invalid_payload(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

