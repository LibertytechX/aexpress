import uuid
from unittest.mock import patch, MagicMock
import pytest

from dispatcher.emails import (
    get_rider_rejection_email_template,
    send_rider_rejection_email,
)
from dispatcher.tasks import send_rider_rejection_email_task
from dispatcher.models import Rider
from riders.models import RiderDocument
from authentication.models import User


class TestRiderRejectionEmailUnit:

    def test_get_rider_rejection_email_template_contains_all_details(self):
        rider_name = "Chidi"
        reason = "The uploaded documents do not match government database records."
        rejected_docs = [
            {
                "name": "Driver's License",
                "reason": "Document has expired.",
            },
            {
                "name": "National ID",
                "reason": "Image is blurry and name is illegible.",
            },
        ]

        html = get_rider_rejection_email_template(
            rider_name=rider_name,
            reason=reason,
            rejected_documents=rejected_docs,
        )

        assert "Chidi" in html
        assert "The uploaded documents do not match government database records." in html
        assert "Driver's License" in html
        assert "Document has expired." in html
        assert "National ID" in html
        assert "Image is blurry and name is illegible." in html
        assert "Documents Requiring Re-upload" in html
        assert "How to Re-submit Your Application" in html

    def test_get_rider_rejection_email_template_without_docs(self):
        rider_name = "Emeka"
        reason = "Application does not satisfy minimum requirements."
        html = get_rider_rejection_email_template(
            rider_name=rider_name,
            reason=reason,
            rejected_documents=[],
        )

        assert "Emeka" in html
        assert "Application does not satisfy minimum requirements." in html
        assert "Documents Requiring Re-upload" not in html


@pytest.mark.django_db
class TestSendRiderRejectionEmail:

    @pytest.fixture(autouse=True)
    def setup_rider(self):
        self.user = User.objects.create_user(
            phone="+2348099887766",
            email="chidi.rider@test.com",
            first_name="Chidi",
            last_name="Okonkwo",
            usertype="Rider",
        )
        self.rider = Rider.objects.get(user=self.user)
        self.rider.rider_id = "100999"
        self.rider.save()

        self.doc1 = RiderDocument.objects.create(
            rider=self.rider,
            doc_type=RiderDocument.DocType.DRIVERS_LICENSE,
            file_url="https://s3.example.com/license.jpg",
            status=RiderDocument.Status.REJECTED,
            rejection_reason="License is expired.",
        )
        self.doc2 = RiderDocument.objects.create(
            rider=self.rider,
            doc_type=RiderDocument.DocType.NATIONAL_ID,
            file_url="https://s3.example.com/nin.jpg",
            status=RiderDocument.Status.REJECTED,
            rejection_reason="NIN slip is blurry.",
        )

    @patch("dispatcher.emails.send_email_with_fallback")
    def test_send_rider_rejection_email_success(self, mock_send):
        mock_send.return_value = True

        result = send_rider_rejection_email(
            rider=self.rider,
            reason="Please update your expired and blurry documents.",
            rejected_doc_ids=[str(self.doc1.id), str(self.doc2.id)],
        )

        assert result is True
        mock_send.assert_called_once()
        kwargs = mock_send.call_args[1]
        assert kwargs["to_email"] == "chidi.rider@test.com"
        assert "Important Update Regarding Your Rider Application" in kwargs["subject"]
        assert "Chidi" in kwargs["html_content"]
        assert "Driver's License" in kwargs["html_content"]
        assert "License is expired." in kwargs["html_content"]
        assert "National ID" in kwargs["html_content"]
        assert "NIN slip is blurry." in kwargs["html_content"]

        # Plain text assertions
        assert "Chidi" in kwargs["text_content"]
        assert "Driver's License: License is expired." in kwargs["text_content"]
        assert "National ID: NIN slip is blurry." in kwargs["text_content"]

    @patch("dispatcher.emails.send_email_with_fallback")
    def test_send_rider_rejection_email_by_uuid_string(self, mock_send):
        mock_send.return_value = True

        result = send_rider_rejection_email(
            rider=str(self.rider.id),
            reason="General rejection",
        )

        assert result is True
        mock_send.assert_called_once()
        kwargs = mock_send.call_args[1]
        assert kwargs["to_email"] == "chidi.rider@test.com"

    @patch("dispatcher.emails.send_email_with_fallback")
    def test_send_rider_rejection_email_rider_not_found(self, mock_send):
        random_id = str(uuid.uuid4())
        result = send_rider_rejection_email(rider=random_id)
        assert result is False
        mock_send.assert_not_called()

    @patch("dispatcher.emails.send_email_with_fallback")
    def test_send_rider_rejection_email_no_email(self, mock_send):
        self.user.email = ""
        self.user.save(update_fields=["email"])

        result = send_rider_rejection_email(rider=self.rider)
        assert result is False
        mock_send.assert_not_called()

    @patch("dispatcher.emails.send_rider_rejection_email")
    def test_send_rider_rejection_email_task_invokes_email_service(self, mock_send_email):
        mock_send_email.return_value = True

        result = send_rider_rejection_email_task(
            rider_id=str(self.rider.id),
            reason="Test reason",
            rejected_doc_ids=[str(self.doc1.id)],
        )

        assert result is True
        mock_send_email.assert_called_once_with(
            str(self.rider.id),
            reason="Test reason",
            rejected_doc_ids=[str(self.doc1.id)],
        )
