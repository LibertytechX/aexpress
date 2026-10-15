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
    SystemSettings,
)
from orders.models import Order, Vehicle
from dispatcher.services import (
    affiliate_rider_to_dispatcher,
    record_dispatcher_affiliation_commission,
    reconcile_dispatcher_monthly_commission,
    reset_monthly_commissions_service,
    get_current_month_str,
    get_previous_month_str,
)


@pytest.mark.django_db
class TestDispatcherAffiliationServices:

    @pytest.fixture(autouse=True)
    def setup_entities(self):
        # Create dispatcher user & profile
        self.dispatcher_user = User.objects.create_user(
            phone="+2348011112222",
            password="password123",
            first_name="Hub",
            last_name="Captain",
            usertype="Dispatcher",
        )
        self.dispatcher_profile = DispatcherProfile.objects.get(user=self.dispatcher_user)
        self.dispatcher_profile.affiliation_code = "HUB123"
        self.dispatcher_profile.role = DispatcherProfile.Role.HUB_CAPTAIN
        self.dispatcher_profile.save()

        # Create second dispatcher
        self.dispatcher_user2 = User.objects.create_user(
            phone="+2348099998888",
            password="password123",
            first_name="Zone",
            last_name="Lead",
            usertype="Dispatcher",
        )
        self.dispatcher_profile2 = DispatcherProfile.objects.get(user=self.dispatcher_user2)
        self.dispatcher_profile2.affiliation_code = "ZONE99"
        self.dispatcher_profile2.role = DispatcherProfile.Role.ZONE_LEAD
        self.dispatcher_profile2.save()

        # Create rider user & profile
        self.rider_user = User.objects.create_user(
            phone="+2348033334444",
            password="password123",
            first_name="John",
            last_name="Rider",
            usertype="Rider",
        )
        self.rider = Rider.objects.get(user=self.rider_user)
        self.rider.rider_id = "100001"
        self.rider.save()

        # Create customer user for orders
        self.customer = User.objects.create_user(
            phone="+2348055556666",
            password="password123",
            first_name="Alice",
            last_name="Merchant",
            usertype="Merchant",
        )

        # Create vehicle for orders
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

        # Set system settings
        self.settings = SystemSettings.objects.first()
        if not self.settings:
            self.settings = SystemSettings.objects.create(
                affiliation_commission_per_order=Decimal("3000.00")
            )
        else:
            self.settings.affiliation_commission_per_order = Decimal("3000.00")
            self.settings.save()

    def test_affiliate_rider_to_dispatcher_success(self):
        """Test rider successfully links to dispatcher via affiliation code."""
        assert not self.rider.is_affiliated
        assert self.rider.affiliated_to is None

        disp = affiliate_rider_to_dispatcher(self.rider, "HUB123")
        self.rider.refresh_from_db()

        assert disp.id == self.dispatcher_profile.id
        assert self.rider.is_affiliated is True
        assert self.rider.affiliated_to == self.dispatcher_profile
        assert self.rider.affiliated_at is not None

    def test_affiliate_rider_case_insensitive_code(self):
        """Affiliation code lookup must be case-insensitive and stripped."""
        disp = affiliate_rider_to_dispatcher(self.rider, "  hub123  ")
        self.rider.refresh_from_db()

        assert disp.id == self.dispatcher_profile.id
        assert self.rider.is_affiliated is True

    def test_affiliate_rider_invalid_code_raises_service_exception(self):
        """Invalid code must raise ServiceException with 400 status."""
        with pytest.raises(ServiceException) as exc:
            affiliate_rider_to_dispatcher(self.rider, "NONEXISTENT")
        assert exc.value.status_code == 400
        assert "Invalid affiliation code" in exc.value.message

    def test_affiliate_rider_already_affiliated_with_same_dispatcher(self):
        """Attempting to affiliate again with the same dispatcher raises ServiceException."""
        affiliate_rider_to_dispatcher(self.rider, "HUB123")
        self.rider.refresh_from_db()

        with pytest.raises(ServiceException) as exc:
            affiliate_rider_to_dispatcher(self.rider, "HUB123")
        assert exc.value.status_code == 400
        assert "already affiliated with this dispatcher" in exc.value.message

    def test_affiliate_rider_already_affiliated_with_different_dispatcher(self):
        """Attempting to affiliate with another dispatcher when already affiliated raises error."""
        affiliate_rider_to_dispatcher(self.rider, "HUB123")
        self.rider.refresh_from_db()

        with pytest.raises(ServiceException) as exc:
            affiliate_rider_to_dispatcher(self.rider, "ZONE99")
        assert exc.value.status_code == 400
        assert "already affiliated" in exc.value.message

    def test_record_commission_unaffiliated_rider_returns_none(self):
        """Orders completed by unaffiliated riders generate no commission."""
        order = Order.objects.create(
            user=self.customer,
            rider=self.rider,
            vehicle=self.vehicle,
            order_number="ORD-1001",
            status="Done",
            total_amount=Decimal("5000.00"),
        )
        commission = record_dispatcher_affiliation_commission(order)
        assert commission is None
        assert DispatcherCommission.objects.count() == 0

    def test_record_commission_affiliated_rider_success(self):
        """Completing an order by an affiliated rider creates commission and updates dispatcher balances."""
        affiliate_rider_to_dispatcher(self.rider, "HUB123")
        self.rider.refresh_from_db()

        order = Order.objects.create(
            user=self.customer,
            rider=self.rider,
            vehicle=self.vehicle,
            order_number="ORD-1002",
            status="Done",
            completed_at=timezone.now(),
            total_amount=Decimal("5000.00"),
        )

        commission = record_dispatcher_affiliation_commission(order)
        assert commission is not None
        assert commission.amount == Decimal("3000.00")
        assert commission.dispatcher == self.dispatcher_profile
        assert commission.rider == self.rider
        assert commission.order == order

        self.dispatcher_profile.refresh_from_db()
        assert self.dispatcher_profile.monthly_commission == Decimal("3000.00")
        assert self.dispatcher_profile.total_commission_earned == Decimal("3000.00")

        # Check monthly summary record
        current_month = get_current_month_str()
        monthly_earning = DispatcherMonthlyEarning.objects.get(
            dispatcher=self.dispatcher_profile, month_year=current_month
        )
        assert monthly_earning.total_orders == 1
        assert monthly_earning.total_commission == Decimal("3000.00")

    def test_record_commission_idempotent(self):
        """Calling record_dispatcher_affiliation_commission multiple times for the same order does not duplicate."""
        affiliate_rider_to_dispatcher(self.rider, "HUB123")
        self.rider.refresh_from_db()

        order = Order.objects.create(
            user=self.customer,
            rider=self.rider,
            vehicle=self.vehicle,
            order_number="ORD-1003",
            status="Done",
            completed_at=timezone.now(),
            total_amount=Decimal("5000.00"),
        )

        comm1 = record_dispatcher_affiliation_commission(order)
        comm2 = record_dispatcher_affiliation_commission(order)

        assert comm1.id == comm2.id
        assert DispatcherCommission.objects.count() == 1

        self.dispatcher_profile.refresh_from_db()
        assert self.dispatcher_profile.monthly_commission == Decimal("3000.00")

    def test_record_multiple_orders_accumulation(self):
        """Multiple completed orders accumulate properly in monthly and lifetime totals."""
        affiliate_rider_to_dispatcher(self.rider, "HUB123")
        self.rider.refresh_from_db()

        for i in range(1, 5):
            order = Order.objects.create(
                user=self.customer,
                rider=self.rider,
                vehicle=self.vehicle,
                order_number=f"ORD-MULTI-{i}",
                status="Done",
                completed_at=timezone.now(),
                total_amount=Decimal("4000.00"),
            )
            record_dispatcher_affiliation_commission(order)

        self.dispatcher_profile.refresh_from_db()
        assert self.dispatcher_profile.monthly_commission == Decimal("12000.00")
        assert self.dispatcher_profile.total_commission_earned == Decimal("12000.00")

        current_month = get_current_month_str()
        earning = DispatcherMonthlyEarning.objects.get(
            dispatcher=self.dispatcher_profile, month_year=current_month
        )
        assert earning.total_orders == 4
        assert earning.total_commission == Decimal("12000.00")

    def test_reconcile_dispatcher_monthly_commission(self):
        """Reconciliation verifies and heals any discrepancies."""
        affiliate_rider_to_dispatcher(self.rider, "HUB123")
        self.rider.refresh_from_db()

        current_month = get_current_month_str()
        order = Order.objects.create(
            user=self.customer,
            rider=self.rider,
            vehicle=self.vehicle,
            order_number="ORD-RECON-1",
            status="Done",
            completed_at=timezone.now(),
            total_amount=Decimal("5000.00"),
        )
        record_dispatcher_affiliation_commission(order)

        # Intentionally alter monthly commission cache
        self.dispatcher_profile.monthly_commission = Decimal("99999.00")
        self.dispatcher_profile.save()

        recon = reconcile_dispatcher_monthly_commission(
            self.dispatcher_profile, month_year=current_month
        )
        assert recon["reconciled"] is True
        assert recon["total_orders"] == 1
        assert Decimal(recon["total_commission"]) == Decimal("3000.00")

        self.dispatcher_profile.refresh_from_db()
        assert self.dispatcher_profile.monthly_commission == Decimal("3000.00")

    def test_reset_monthly_commissions_service(self):
        """Monthly rollover moves monthly_commission to previous_month_commission and resets active to 0."""
        self.dispatcher_profile.monthly_commission = Decimal("15000.00")
        self.dispatcher_profile.previous_month_commission = Decimal("0.00")
        # Mark as previous month
        self.dispatcher_profile.last_commission_month = "2026-09"
        self.dispatcher_profile.save()

        count = reset_monthly_commissions_service()
        assert count >= 1

        self.dispatcher_profile.refresh_from_db()
        assert self.dispatcher_profile.previous_month_commission == Decimal("15000.00")
        assert self.dispatcher_profile.monthly_commission == Decimal("0.00")
        assert self.dispatcher_profile.last_commission_month == get_current_month_str()
