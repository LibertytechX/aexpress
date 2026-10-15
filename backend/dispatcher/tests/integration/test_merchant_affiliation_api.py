import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient

from authentication.models import User
from authentication.serializers import SignupSerializer
from dispatcher.models import (
    DispatcherProfile,
    DispatcherCommission,
    Merchant,
    Rider,
    SystemSettings,
)
from orders.models import Order, Vehicle
from dispatcher.services import affiliate_merchant_to_dispatcher, record_dispatcher_affiliation_commission


@pytest.mark.django_db
class TestMerchantAffiliationAPI:

    @pytest.fixture(autouse=True)
    def setup_api_data(self):
        self.client = APIClient()

        # Create Dispatcher
        self.dispatcher_user = User.objects.create_user(
            phone="+2348011112222",
            password="password123",
            first_name="Hub",
            last_name="Captain",
            usertype="Dispatcher",
        )
        self.dispatcher_profile = DispatcherProfile.objects.get(user=self.dispatcher_user)
        self.dispatcher_profile.affiliation_code = "HUBTEST"
        self.dispatcher_profile.role = DispatcherProfile.Role.HUB_CAPTAIN
        self.dispatcher_profile.save()

        # Create Merchant
        self.merchant_user = User.objects.create_user(
            phone="+2348077778888",
            email="merchant@test.com",
            business_name="Test Store",
            contact_name="Bob Builder",
            password="password123",
            usertype="Merchant",
        )
        self.merchant = Merchant.objects.get(user=self.merchant_user)

        # Create Rider
        self.rider_user = User.objects.create_user(
            phone="+2348033334444",
            password="password123",
            first_name="Speedy",
            last_name="Rider",
            usertype="Rider",
        )
        self.rider = Rider.objects.get(user=self.rider_user)
        self.rider.rider_id = "R99999"
        self.rider.save()

        # Vehicle & Settings
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
        self.settings = SystemSettings.objects.first()
        if not self.settings:
            self.settings = SystemSettings.objects.create(
                affiliation_commission_per_order=Decimal("3000.00")
            )
        else:
            self.settings.affiliation_commission_per_order = Decimal("3000.00")
            self.settings.save()

    def test_merchant_affiliation_get_unaffiliated(self):
        """Unaffiliated merchant queries affiliation status."""
        self.client.force_authenticate(user=self.merchant_user)
        res = self.client.get("/api/auth/merchant/affiliation/")
        assert res.status_code == 200
        assert res.data["status"] == "success"
        assert res.data["data"]["is_affiliated"] is False
        assert res.data["data"]["affiliation_code"] is None

    def test_merchant_affiliation_post_success(self):
        """Merchant links to dispatcher via POST with affiliation code."""
        self.client.force_authenticate(user=self.merchant_user)
        res = self.client.post(
            "/api/auth/merchant/affiliation/",
            data={"affiliation_code": "HUBTEST"},
            format="json",
        )
        assert res.status_code == 200
        assert res.data["status"] == "success"
        assert res.data["data"]["is_affiliated"] is True
        assert res.data["data"]["affiliation_code"] == "HUBTEST"
        assert "Hub Captain" in res.data["data"]["dispatcher_name"]

        self.merchant.refresh_from_db()
        assert self.merchant.is_affiliated is True
        assert self.merchant.affiliated_to == self.dispatcher_profile

    def test_merchant_affiliation_post_invalid_code(self):
        """Merchant attempts to link with invalid code."""
        self.client.force_authenticate(user=self.merchant_user)
        res = self.client.post(
            "/api/auth/merchant/affiliation/",
            data={"affiliation_code": "WRONGCODE"},
            format="json",
        )
        assert res.status_code == 400
        assert res.data["status"] == "error"

    def test_dispatcher_summary_includes_merchant_metrics(self):
        """Dispatcher summary endpoint includes affiliated merchants metrics."""
        affiliate_merchant_to_dispatcher(self.merchant, "HUBTEST")

        self.client.force_authenticate(user=self.dispatcher_user)
        res = self.client.get("/api/dispatch/affiliation/summary/")
        assert res.status_code == 200
        data = res.data["data"]
        assert data["total_affiliated_merchants"] == 1
        assert data["affiliated_merchants_count"] == 1

    def test_dispatcher_affiliated_merchants_list_api(self):
        """Dispatcher lists their affiliated merchants."""
        affiliate_merchant_to_dispatcher(self.merchant, "HUBTEST")

        # Create an order
        order = Order.objects.create(
            order_number="ORD-MERCH-API",
            user=self.merchant_user,
            rider=self.rider,
            vehicle=self.vehicle,
            pickup_address="Ikeja, Lagos",
            sender_name="Test Store",
            sender_phone="08077778888",
            total_amount=Decimal("4000.00"),
            status="Done",
            completed_at=timezone.now(),
        )
        record_dispatcher_affiliation_commission(order)

        self.client.force_authenticate(user=self.dispatcher_user)
        res = self.client.get("/api/dispatch/affiliation/merchants/")
        assert res.status_code == 200
        assert res.data["status"] == "success"
        results = res.data["data"]
        assert len(results) == 1
        item = results[0]
        assert item["merchant_id"] == self.merchant.merchant_id
        assert item["business_name"] == "Test Store"
        assert item["orders_this_month"] == 1
        assert item["commission_this_month"] == "3000.00"

    def test_dispatcher_commissions_list_with_merchant_info(self):
        """Dispatcher queries commissions list and sees merchant source and details."""
        affiliate_merchant_to_dispatcher(self.merchant, "HUBTEST")

        order = Order.objects.create(
            order_number="ORD-COMM-API",
            user=self.merchant_user,
            rider=self.rider,
            vehicle=self.vehicle,
            pickup_address="Marina, Lagos",
            sender_name="Test Store",
            sender_phone="08077778888",
            total_amount=Decimal("3500.00"),
            status="Done",
            completed_at=timezone.now(),
        )
        record_dispatcher_affiliation_commission(order)

        self.client.force_authenticate(user=self.dispatcher_user)
        res = self.client.get("/api/dispatch/affiliation/commissions/?merchant_id=" + self.merchant.merchant_id)
        assert res.status_code == 200
        results = res.data["data"]["results"]
        assert len(results) == 1
        comm = results[0]
        assert comm["merchant_id"] == self.merchant.merchant_id
        assert comm["merchant_name"] == "Test Store"
        assert comm["affiliation_source"] == "merchant"
        assert comm["amount"] == "3000.00"

    def test_signup_serializer_with_affiliation_code(self):
        """SignupSerializer links newly registered merchant to dispatcher using code."""
        payload = {
            "phone": "+2348055556666",
            "email": "newmerchant@example.com",
            "business_name": "New Bakery",
            "contact_name": "Carol Danvers",
            "address": "10 Surulere, Lagos",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "usertype": "Merchant",
            "affiliation_code": "HUBTEST",
        }
        serializer = SignupSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        user = serializer.save()

        merchant = Merchant.objects.get(user=user)
        assert merchant.is_affiliated is True
        assert merchant.affiliated_to == self.dispatcher_profile
