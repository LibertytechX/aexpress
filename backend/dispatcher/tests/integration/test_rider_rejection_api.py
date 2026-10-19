from unittest.mock import patch
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from authentication.models import User
from dispatcher.models import DispatcherProfile, Rider
from riders.models import RiderDocument


@pytest.mark.django_db
class TestRiderRejectionAPIIntegration:

    @pytest.fixture(autouse=True)
    def setup_entities(self):
        self.client = APIClient()

        # Create dispatcher admin user & profile
        self.admin_user = User.objects.create_user(
            phone="+2348011223344",
            email="admin.dispatch@aexpress.com",
            password="Password123!",
            first_name="Operations",
            last_name="Admin",
            usertype="Dispatcher",
        )
        self.dispatcher_profile = DispatcherProfile.objects.get(user=self.admin_user)
        self.dispatcher_profile.role = DispatcherProfile.Role.ADMIN
        self.dispatcher_profile.save()

        # Create regular (non-admin) dispatcher user
        self.regular_dispatcher = User.objects.create_user(
            phone="+2348055667788",
            email="regular.dispatch@aexpress.com",
            password="Password123!",
            first_name="Regular",
            last_name="Dispatcher",
            usertype="Dispatcher",
        )
        self.reg_profile = DispatcherProfile.objects.get(user=self.regular_dispatcher)
        self.reg_profile.role = DispatcherProfile.Role.ZONE_LEAD
        self.reg_profile.save()
        self.regular_dispatcher.refresh_from_db()

        # Create a self-registered rider
        self.rider_user = User.objects.create_user(
            phone="+2348123456789",
            email="tunde.rider@aexpress.com",
            password="Password123!",
            first_name="Tunde",
            last_name="Bakare",
            usertype="Rider",
        )
        self.rider = Rider.objects.get(user=self.rider_user)
        self.rider.rider_id = "200001"
        self.rider.approval_status = Rider.ApprovalStatus.PENDING
        self.rider.is_independent_rider = True
        self.rider.is_authorized = False
        self.rider.save()

        # Create KYC documents for the rider
        self.license_doc = RiderDocument.objects.create(
            rider=self.rider,
            doc_type=RiderDocument.DocType.DRIVERS_LICENSE,
            file_url="https://s3.aexpress.com/docs/license.jpg",
            status=RiderDocument.Status.PENDING,
        )
        self.insurance_doc = RiderDocument.objects.create(
            rider=self.rider,
            doc_type=RiderDocument.DocType.VEHICLE_INSURANCE,
            file_url="https://s3.aexpress.com/docs/insurance.jpg",
            status=RiderDocument.Status.PENDING,
        )

        self.url = f"/api/dispatch/riders/{self.rider.id}/reject/"

    @patch("dispatcher.emails.send_email_with_fallback")
    @patch("dispatcher.views.notify_rider")
    def test_reject_rider_sends_email_with_documents_and_reasons(
        self, mock_notify_rider, mock_send_email
    ):
        mock_send_email.return_value = True

        self.client.force_authenticate(user=self.admin_user)

        payload = {
            "reason": "Submitted KYC documents failed compliance checks.",
            "rejected_documents": [
                {
                    "document_id": str(self.license_doc.id),
                    "reason": "Driver's license photo is blurry and illegible.",
                },
                {
                    "document_id": str(self.insurance_doc.id),
                    "reason": "Vehicle insurance policy has expired.",
                },
            ],
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        # Verify DB updates
        self.rider.refresh_from_db()
        assert self.rider.approval_status == Rider.ApprovalStatus.REJECTED
        assert self.rider.is_authorized is False
        assert self.rider.rejection_reason == payload["reason"]

        self.license_doc.refresh_from_db()
        assert self.license_doc.status == RiderDocument.Status.REJECTED
        assert (
            self.license_doc.rejection_reason
            == "Driver's license photo is blurry and illegible."
        )

        self.insurance_doc.refresh_from_db()
        assert self.insurance_doc.status == RiderDocument.Status.REJECTED
        assert (
            self.insurance_doc.rejection_reason
            == "Vehicle insurance policy has expired."
        )

        # Verify push notification
        mock_notify_rider.assert_called_once_with(
            self.rider,
            "Application Rejected",
            payload["reason"],
        )

        # Verify email was sent to rider with document details
        mock_send_email.assert_called_once()
        email_kwargs = mock_send_email.call_args[1]
        assert email_kwargs["to_email"] == "tunde.rider@aexpress.com"
        assert "Important Update Regarding Your Rider Application" in email_kwargs["subject"]

        # Check HTML content contains rider name, overall reason, and document reasons
        html = email_kwargs["html_content"]
        assert "Tunde" in html
        assert payload["reason"] in html
        assert "Driver's License" in html
        assert "Driver's license photo is blurry and illegible." in html
        assert "Vehicle Insurance" in html
        assert "Vehicle insurance policy has expired." in html

        # Check plain text content contains same information
        text = email_kwargs["text_content"]
        assert "Tunde" in text
        assert payload["reason"] in text
        assert "Driver's License: Driver's license photo is blurry and illegible." in text
        assert "Vehicle Insurance: Vehicle insurance policy has expired." in text

    @patch("dispatcher.emails.send_email_with_fallback")
    def test_reject_rider_without_specific_docs(self, mock_send_email):
        mock_send_email.return_value = True

        self.client.force_authenticate(user=self.admin_user)

        payload = {
            "reason": "Applicant did not meet age requirement.",
            "rejected_documents": [],
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        self.rider.refresh_from_db()
        assert self.rider.approval_status == Rider.ApprovalStatus.REJECTED
        assert self.rider.rejection_reason == payload["reason"]

        # Email should still be sent explaining overall rejection
        mock_send_email.assert_called_once()
        email_kwargs = mock_send_email.call_args[1]
        assert email_kwargs["to_email"] == "tunde.rider@aexpress.com"
        assert "Applicant did not meet age requirement." in email_kwargs["html_content"]

    def test_reject_rider_with_nonexistent_document_returns_400(self):
        self.client.force_authenticate(user=self.admin_user)

        import uuid
        fake_doc_id = str(uuid.uuid4())

        payload = {
            "reason": "Test rejection",
            "rejected_documents": [
                {
                    "document_id": fake_doc_id,
                    "reason": "Bad doc",
                }
            ],
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert f"Document {fake_doc_id} not found for this rider." in response.data["message"]

    def test_reject_rider_requires_dispatcher_admin_permission(self):
        # Non-admin dispatcher should be forbidden
        self.client.force_authenticate(user=self.regular_dispatcher)

        payload = {
            "reason": "Unauthorized attempt",
            "rejected_documents": [],
        }

        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
