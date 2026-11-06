import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from sparky_utils.exceptions import ServiceException

from authentication.models import User
from dispatcher.models import (
    DispatcherProfile,
    DispatcherCommission,
    DispatcherMonthlyEarning,
    Rider,
    Merchant,
    SystemSettings,
)
from orders.models import Order, Vehicle
from dispatcher.services import (
    affiliate_merchant_to_dispatcher,
    affiliate_rider_to_dispatcher,
    record_dispatcher_affiliation_commission,
    reconcile_dispatcher_monthly_commission,
    reset_monthly_commissions_service,
    get_current_month_str,
)


@pytest.mark.django_db
class TestMerchantAffiliationServices:

    @pytest.fixture(autouse=True)
    def setup_entities(self):
        # Create dispatcher 1 (Hub Captain)
        self.disp_user1 = User.objects.create_user(
            phone="+2348011112222",
            password="password123",
            first_name="Hub",
            last_name="Captain",
            usertype="Dispatcher",
        )
        self.disp1 = DispatcherProfile.objects.get(user=self.disp_user1)
        self.disp1.affiliation_code = "HUB001"
        self.disp1.role = DispatcherProfile.Role.HUB_CAPTAIN
        self.disp1.save()

        # Create dispatcher 2 (Zone Lead)
        self.disp_user2 = User.objects.create_user(
            phone="+2348099998888",
            password="password123",
            first_name="Zone",
            last_name="Lead",
            usertype="Dispatcher",
        )
        self.disp2 = DispatcherProfile.objects.get(user=self.disp_user2)
        self.disp2.affiliation_code = "ZONE002"
        self.disp2.role = DispatcherProfile.Role.ZONE_LEAD
        self.disp2.save()

        # Create Merchant
        self.merchant_user = User.objects.create_user(
            phone="+2348077778888",
            email="merchant@example.com",
            business_name="Acme Foods",
            contact_name="Alice Smith",
            password="password123",
            usertype="Merchant",
        )
        self.merchant = Merchant.objects.get(user=self.merchant_user)

        # Create Rider
        self.rider_user = User.objects.create_user(
            phone="+2348033334444",
            password="password123",
            first_name="Test",
            last_name="Rider",
            usertype="Rider",
        )
        self.rider = Rider.objects.get(user=self.rider_user)
        self.rider.rider_id = "R10001"
        self.rider.save()

        # Create Vehicle
        self.vehicle = Vehicle.objects.create(
            name="Motorcycle",
            max_weight_kg=20,
            base_price=500,
            base_fare=500,
            rate_per_km=100,
            rate_per_minute=10,
            min_distance_km=2,
            min_fee=1000,
        )

        # Settings
        self.settings = SystemSettings.objects.first()
        if not self.settings:
            self.settings = SystemSettings.objects.create(
                affiliation_commission_per_order=Decimal("3000.00")
            )
        else:
            self.settings.affiliation_commission_per_order = Decimal("3000.00")
            self.settings.save()

    def test_affiliate_merchant_success(self):
        """Test merchant successfully links to dispatcher using affiliation code."""
        assert not self.merchant.is_affiliated
        assert self.merchant.affiliated_to is None

        disp = affiliate_merchant_to_dispatcher(self.merchant, "HUB001")
        assert disp.id == self.disp1.id

        self.merchant.refresh_from_db()
        assert self.merchant.is_affiliated is True
        assert self.merchant.affiliated_to == self.disp1
        assert self.merchant.affiliated_at is not None

        self.disp1.refresh_from_db()
        assert self.disp1.affiliated_merchants_count == 1

    def test_affiliate_merchant_case_insensitive(self):
        """Test code matching is case-insensitive and ignores surrounding whitespace."""
        affiliate_merchant_to_dispatcher(self.merchant, "  hub001  ")
        self.merchant.refresh_from_db()
        assert self.merchant.affiliated_to == self.disp1

    def test_affiliate_merchant_invalid_code(self):
        """Test invalid code raises ServiceException."""
        with pytest.raises(ServiceException) as exc:
            affiliate_merchant_to_dispatcher(self.merchant, "NONEXISTENT")
        assert exc.value.status_code == 400
        assert "Invalid affiliation code" in str(exc.value.message)

    def test_affiliate_merchant_already_affiliated_same(self):
        """Test re-affiliating with same dispatcher raises ServiceException."""
        affiliate_merchant_to_dispatcher(self.merchant, "HUB001")
        with pytest.raises(ServiceException) as exc:
            affiliate_merchant_to_dispatcher(self.merchant, "HUB001")
        assert exc.value.status_code == 400
        assert "already affiliated with this dispatcher" in str(exc.value.message)

    def test_affiliate_merchant_already_affiliated_different(self):
        """Test re-affiliating with different dispatcher is blocked."""
        affiliate_merchant_to_dispatcher(self.merchant, "HUB001")
        with pytest.raises(ServiceException) as exc:
            affiliate_merchant_to_dispatcher(self.merchant, "ZONE002")
        assert exc.value.status_code == 400
        assert "already affiliated with" in str(exc.value.message)

    def test_order_completion_merchant_commission_only(self):
        """When only merchant is affiliated, its dispatcher earns ₦3,000 commission."""
        affiliate_merchant_to_dispatcher(self.merchant, "HUB001")

        order = Order.objects.create(
            order_number="ORD-M001",
            user=self.merchant_user,
            rider=self.rider,
            vehicle=self.vehicle,
            pickup_address="123 Ikeja, Lagos",
            sender_name="Acme",
            sender_phone="08077778888",
            total_amount=Decimal("5000.00"),
            status="Done",
            completed_at=timezone.now(),
        )

        commissions = record_dispatcher_affiliation_commission(order)
        assert len(commissions) == 1
        comm = commissions[0]
        assert comm.dispatcher == self.disp1
        assert comm.merchant == self.merchant
        assert comm.rider is None
        assert comm.affiliation_source == "merchant"
        assert comm.amount == Decimal("3000.00")

        self.disp1.refresh_from_db()
        assert self.disp1.monthly_commission == Decimal("3000.00")
        assert self.disp1.total_commission_earned == Decimal("3000.00")

    def test_order_completion_same_dispatcher_deduplication(self):
        """
        CRITICAL USER REQUIREMENT:
        When BOTH the rider and merchant are affiliated to the SAME dispatcher,
        only ONE commission (₦3,000) is awarded to that dispatcher.
        The rider commission is disregarded to prevent double payout.
        """
        affiliate_rider_to_dispatcher(self.rider, "HUB001")
        affiliate_merchant_to_dispatcher(self.merchant, "HUB001")

        order = Order.objects.create(
            order_number="ORD-SAME-DISP",
            user=self.merchant_user,
            rider=self.rider,
            vehicle=self.vehicle,
            pickup_address="456 Victoria Island, Lagos",
            sender_name="Acme",
            sender_phone="08077778888",
            total_amount=Decimal("5000.00"),
            status="Done",
            completed_at=timezone.now(),
        )

        commissions = record_dispatcher_affiliation_commission(order)
        assert len(commissions) == 1
        comm = commissions[0]
        assert comm.dispatcher == self.disp1
        assert comm.merchant == self.merchant
        assert comm.amount == Decimal("3000.00")
        assert "single commission awarded" in comm.description

        self.disp1.refresh_from_db()
        # Exactly 3,000, NOT 6,000!
        assert self.disp1.monthly_commission == Decimal("3000.00")
        assert self.disp1.total_commission_earned == Decimal("3000.00")

        # Check monthly earning record
        curr_month = get_current_month_str()
        earning = DispatcherMonthlyEarning.objects.get(
            dispatcher=self.disp1, month_year=curr_month
        )
        assert earning.total_orders == 1
        assert earning.total_commission == Decimal("3000.00")

    def test_order_completion_different_dispatchers(self):
        """
        When Rider is affiliated to Dispatcher 1 and Merchant is affiliated to Dispatcher 2,
        each dispatcher receives their respective 1 commission.
        """
        affiliate_rider_to_dispatcher(self.rider, "HUB001")
        affiliate_merchant_to_dispatcher(self.merchant, "ZONE002")

        order = Order.objects.create(
            order_number="ORD-DIFF-DISP",
            user=self.merchant_user,
            rider=self.rider,
            vehicle=self.vehicle,
            pickup_address="789 Lekki, Lagos",
            sender_name="Acme",
            sender_phone="08077778888",
            total_amount=Decimal("6000.00"),
            status="Done",
            completed_at=timezone.now(),
        )

        commissions = record_dispatcher_affiliation_commission(order)
        assert len(commissions) == 2

        self.disp1.refresh_from_db()
        self.disp2.refresh_from_db()

        # Each dispatcher got 3,000
        assert self.disp1.monthly_commission == Decimal("3000.00")
        assert self.disp2.monthly_commission == Decimal("3000.00")

        # Dispatcher 1 got rider commission
        comm1 = DispatcherCommission.objects.get(dispatcher=self.disp1, order=order)
        assert comm1.affiliation_source == "rider"
        assert comm1.rider == self.rider

        # Dispatcher 2 got merchant commission
        comm2 = DispatcherCommission.objects.get(dispatcher=self.disp2, order=order)
        assert comm2.affiliation_source == "merchant"
        assert comm2.merchant == self.merchant

    def test_order_completion_idempotency(self):
        """Calling record_dispatcher_affiliation_commission repeatedly does not duplicate."""
        affiliate_merchant_to_dispatcher(self.merchant, "HUB001")

        order = Order.objects.create(
            order_number="ORD-IDEMPOTENT",
            user=self.merchant_user,
            rider=self.rider,
            vehicle=self.vehicle,
            pickup_address="100 Yaba, Lagos",
            sender_name="Acme",
            sender_phone="08077778888",
            total_amount=Decimal("4000.00"),
            status="Done",
            completed_at=timezone.now(),
        )

        comm1 = record_dispatcher_affiliation_commission(order)
        comm2 = record_dispatcher_affiliation_commission(order)

        assert len(comm1) == 1
        assert len(comm2) == 1
        assert comm1[0].id == comm2[0].id

        self.disp1.refresh_from_db()
        assert self.disp1.monthly_commission == Decimal("3000.00")
        assert DispatcherCommission.objects.filter(order=order).count() == 1

    def test_reconcile_with_merchant_commissions(self):
        """Reconciliation accurately tallies merchant commissions into monthly earnings."""
        affiliate_merchant_to_dispatcher(self.merchant, "HUB001")

        order = Order.objects.create(
            order_number="ORD-REC-M",
            user=self.merchant_user,
            rider=self.rider,
            vehicle=self.vehicle,
            pickup_address="200 Marina, Lagos",
            sender_name="Acme",
            sender_phone="08077778888",
            total_amount=Decimal("4500.00"),
            status="Done",
            completed_at=timezone.now(),
        )

        record_dispatcher_affiliation_commission(order)

        result = reconcile_dispatcher_monthly_commission(self.disp1)
        assert result["total_orders"] == 1
        assert Decimal(result["total_commission"]) == Decimal("3000.00")
