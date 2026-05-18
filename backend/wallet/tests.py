from django.contrib.admin.sites import AdminSite
from django.db.models.signals import post_save
from django.test import TestCase
from authentication.models import User
from wallet.models import AmortizationWallet, AmortizationTransaction, AmortizationVirtualAccount
from wallet.admin import AmortizationWalletAdmin, AmortizationTransactionAdmin, AmortizationVirtualAccountAdmin
from wallet.signals import create_amortization_wallet_account_detail


class MockRequest:
    """Mock request class for admin testing."""
    pass


class AmortizationAdminSearchTest(TestCase):
    """Test suite for Amortization Django admin search functionality."""

    site: AdminSite
    user: User
    wallet: AmortizationWallet
    transaction: AmortizationTransaction
    virtual_account: AmortizationVirtualAccount

    def setUp(self) -> None:
        """Set up test data and disconnect external integration signals."""
        # Disconnect signal to prevent external API calls during tests
        post_save.disconnect(create_amortization_wallet_account_detail, sender=AmortizationWallet)

        self.site = AdminSite()
        self.user = User.objects.create_user(
            phone="08011112222",
            email="testuser@example.com",
            password="testpassword",
            first_name="Olabode",
            last_name="Olaniyi",
            contact_name="Bode"
        )
        self.wallet = AmortizationWallet.objects.create(
            user=self.user,
            balance=1000.0,
            cost=2000.0,
            expected_daily_payment=100.0
        )
        self.transaction = AmortizationTransaction.objects.create(
            amortization_wallet=self.wallet,
            amount=100.0,
            entry_type="credit",
            reference="TEST-REF-123",
            description="Daily payment",
            balance_before=900.0,
            balance_after=1000.0,
            status="completed"
        )
        self.virtual_account = AmortizationVirtualAccount.objects.create(
            user=self.user,
            account_number="9988776655",
            account_name="AX-AMORT-OLABODE",
            bank_name="Test Bank",
            bank_code="123",
            corebanking_account_id="cb-123",
            is_active=True
        )

    def tearDown(self) -> None:
        """Clean up test setup and reconnect signals."""
        # Reconnect signal for subsequent test suites
        post_save.connect(create_amortization_wallet_account_detail, sender=AmortizationWallet)
        super().tearDown()

    def test_amortization_wallet_admin_search(self) -> None:
        """Test searching on AmortizationWalletAdmin with first_name, last_name, and contact_name."""
        model_admin: AmortizationWalletAdmin = AmortizationWalletAdmin(AmortizationWallet, self.site)
        
        # Test searching by first name
        queryset = AmortizationWallet.objects.all()
        results_queryset, use_distinct = model_admin.get_search_results(
            MockRequest(), queryset, "Olabode"
        )
        self.assertEqual(results_queryset.count(), 1)

        # Test searching by last name
        results_queryset, use_distinct = model_admin.get_search_results(
            MockRequest(), queryset, "Olaniyi"
        )
        self.assertEqual(results_queryset.count(), 1)

        # Test searching by contact name
        results_queryset, use_distinct = model_admin.get_search_results(
            MockRequest(), queryset, "Bode"
        )
        self.assertEqual(results_queryset.count(), 1)

    def test_amortization_transaction_admin_search(self) -> None:
        """Test searching on AmortizationTransactionAdmin with reference, description, first_name, last_name, and contact_name."""
        model_admin: AmortizationTransactionAdmin = AmortizationTransactionAdmin(AmortizationTransaction, self.site)
        
        # Test searching by user first name
        queryset = AmortizationTransaction.objects.all()
        results_queryset, use_distinct = model_admin.get_search_results(
            MockRequest(), queryset, "Olabode"
        )
        self.assertEqual(results_queryset.count(), 1)

        # Test searching by reference
        results_queryset, use_distinct = model_admin.get_search_results(
            MockRequest(), queryset, "TEST-REF"
        )
        self.assertEqual(results_queryset.count(), 1)

    def test_amortization_virtual_account_admin_search(self) -> None:
        """Test searching on AmortizationVirtualAccountAdmin with bank details and name parts."""
        model_admin: AmortizationVirtualAccountAdmin = AmortizationVirtualAccountAdmin(AmortizationVirtualAccount, self.site)
        
        # Test searching by user last name
        queryset = AmortizationVirtualAccount.objects.all()
        results_queryset, use_distinct = model_admin.get_search_results(
            MockRequest(), queryset, "Olaniyi"
        )
        self.assertEqual(results_queryset.count(), 1)

        # Test searching by account number
        results_queryset, use_distinct = model_admin.get_search_results(
            MockRequest(), queryset, "998877"
        )
        self.assertEqual(results_queryset.count(), 1)
