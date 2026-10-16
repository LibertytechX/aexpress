import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from sparky_utils.exceptions import ServiceException
from wallet.models import Bank, RiderPayoutTransaction, Wallet
from wallet.integrations import (
    LibertyPayAccountEnquiryService,
    WemaCoreBankingPayoutSDK,
)
from riders.serializers import (
    BankListSerializer,
    VerifyAccountSerializer,
    RiderWithdrawalSerializer,
)
from riders.tasks import check_pending_rider_payout_status
from dispatcher.models import Rider
from authentication.models import User


@pytest.mark.django_db
class TestWithdrawalSerializers:
    def test_bank_list_serializer(self):
        bank = Bank.objects.create(
            name="Test Access Bank",
            bank_code="044",
            cbn_code="000014",
            bank_short_name="ACCESS",
            ussd_short_code="*901#",
        )
        serializer = BankListSerializer(bank)
        assert serializer.data["name"] == "Test Access Bank"
        assert serializer.data["bank_code"] == "044"
        assert serializer.data["cbn_code"] == "000014"

    def test_verify_account_serializer_valid(self):
        data = {"account_number": "0123456789", "bank_code": "044"}
        serializer = VerifyAccountSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["account_number"] == "0123456789"
        assert serializer.validated_data["bank_code"] == "044"

    def test_verify_account_serializer_invalid_account_number(self):
        data = {"account_number": "123", "bank_code": "044"}
        serializer = VerifyAccountSerializer(data=data)
        with pytest.raises(ServiceException) as exc:
            serializer.is_valid(raise_exception=True)
        assert exc.value.status_code == 400
        assert "Account number must be a valid 10-digit" in exc.value.message

    def test_verify_account_serializer_missing_fields(self):
        data = {"account_number": "", "bank_code": ""}
        serializer = VerifyAccountSerializer(data=data)
        assert not serializer.is_valid()

    def test_rider_withdrawal_serializer_valid(self):
        data = {
            "amount": "1500.00",
            "account_number": "0123456789",
            "account_name": "John Doe",
            "bank_code": "044",
            "bank_name": "Access Bank",
            "narration": "Trip earnings",
        }
        serializer = RiderWithdrawalSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["amount"] == Decimal("1500.00")

    def test_rider_withdrawal_serializer_min_amount(self):
        data = {
            "amount": "50.00",
            "account_number": "0123456789",
            "account_name": "John Doe",
            "bank_code": "044",
        }
        serializer = RiderWithdrawalSerializer(data=data)
        with pytest.raises(ServiceException) as exc:
            serializer.is_valid(raise_exception=True)
        assert exc.value.status_code == 400
        assert "Minimum withdrawal amount is ₦100.00" in exc.value.message

    def test_rider_withdrawal_serializer_missing_account_name(self):
        data = {
            "amount": "500.00",
            "account_number": "0123456789",
            "account_name": "",
            "bank_code": "044",
        }
        serializer = RiderWithdrawalSerializer(data=data)
        assert serializer.is_valid() is False
        assert "account_name" in serializer.errors


@pytest.mark.django_db
class TestLibertyPayAccountEnquiryService:
    @patch("requests.post")
    def test_verify_account_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "account_name": "JANE RIDER",
                "account_number": "0123456789",
                "bank_code": "000014",
                "currency_code": "NGN",
            },
        }
        mock_post.return_value = mock_response

        service = LibertyPayAccountEnquiryService()
        result = service.verify_account("0123456789", "044")

        assert result is not None
        assert result["account_name"] == "JANE RIDER"
        assert result["account_number"] == "0123456789"
        assert result["currency_code"] == "NGN"

    @patch("requests.post")
    def test_verify_account_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Account not found"
        mock_post.return_value = mock_response

        service = LibertyPayAccountEnquiryService()
        result = service.verify_account("0000000000", "044")
        assert result is None


@pytest.mark.django_db
class TestWemaCoreBankingPayoutSDK:
    @patch("requests.post")
    def test_login_and_transfer_success(self, mock_post):
        # 1. Login mock
        mock_login_resp = MagicMock()
        mock_login_resp.status_code = 200
        mock_login_resp.json.return_value = {"data": {"access": "fake-jwt-token"}}

        # 2. Transfer mock
        mock_transfer_resp = MagicMock()
        mock_transfer_resp.status_code = 200
        mock_transfer_resp.json.return_value = {
            "status": "success",
            "data": {"reference": "WDR-123456", "status": "Successful"},
        }

        mock_post.side_effect = [mock_login_resp, mock_transfer_resp]

        sdk = WemaCoreBankingPayoutSDK(mode="LIVE")
        sdk.email = "test@libertypay.com"
        sdk.password = "password"
        sdk.source_account = "0123456789"

        success, data = sdk.transfer_funds(
            amount=1000.0,
            narration="Test withdrawal",
            account_name="Jane Rider",
            account_number="9876543210",
            bank_code="044",
            reference="WDR-123456",
        )

        assert success is True
        assert data["reference"] == "WDR-123456"


@pytest.mark.django_db
class TestReconciliationTask:
    @patch.object(WemaCoreBankingPayoutSDK, "verify_status")
    def test_reconciliation_task_success(self, mock_verify):
        mock_verify.return_value = (True, {"status": "success", "reference": "WDR-TEST-1"})

        user = User.objects.create_user(phone="08099990001", password="pw", first_name="Rider", last_name="One")
        rider = Rider.objects.create(user=user, rider_id="R10001", is_independent_rider=True)
        payout = RiderPayoutTransaction.objects.create(
            rider=rider,
            destination_account_name="Rider One",
            destination_account_number="0123456789",
            destination_bank_code="044",
            amount=Decimal("1000.00"),
            reference="WDR-TEST-1",
            status=RiderPayoutTransaction.Status.PENDING,
        )

        msg = check_pending_rider_payout_status()
        assert "Processed 1 pending payouts" in msg

        payout.refresh_from_db()
        assert payout.status == RiderPayoutTransaction.Status.SUCCESS

    @patch.object(WemaCoreBankingPayoutSDK, "verify_status")
    def test_reconciliation_task_failure_triggers_refund(self, mock_verify):
        mock_verify.return_value = (True, {"status": "failed", "reference": "WDR-TEST-2"})

        user = User.objects.create_user(phone="08099990002", password="pw", first_name="Rider", last_name="Two")
        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.balance = Decimal("500.00")
        wallet.save()
        rider = Rider.objects.create(user=user, rider_id="R10002", is_independent_rider=True)
        payout = RiderPayoutTransaction.objects.create(
            rider=rider,
            destination_account_name="Rider Two",
            destination_account_number="0123456789",
            destination_bank_code="044",
            amount=Decimal("1000.00"),
            reference="WDR-TEST-2",
            status=RiderPayoutTransaction.Status.PENDING,
        )

        msg = check_pending_rider_payout_status()
        assert "Processed 1 pending payouts" in msg

        payout.refresh_from_db()
        assert payout.status == RiderPayoutTransaction.Status.FAILED
        assert payout.refunded is True

        wallet.refresh_from_db()
        # Initial 500 + refunded 1000 = 1500
        assert wallet.balance == Decimal("1500.00")
