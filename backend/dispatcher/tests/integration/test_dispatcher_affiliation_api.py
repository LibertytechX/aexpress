import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient

from authentication.models import User
from dispatcher.models import (
    DispatcherProfile,
    DispatcherCommission,
    DispatcherMonthlyEarning,
    Rider,
    SystemSettings,
)
from orders.models import Order, Vehicle
from dispatcher.services import get_current_month_str


@pytest.mark.django_db
class TestRiderAffiliationAPI:

    @pytest.fixture(autouse=True)
    def setup_entities(self):
        self.client = APIClient()

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

        # Create system settings
        self.settings = SystemSettings.objects.first()
        if not self.settings:
            self.settings = SystemSettings.objects.create(
                affiliation_commission_per_order=Decimal("3000.00")
            )
        else:
            self.settings.affiliation_commission_per_order = Decimal("3000.00")
            self.settings.save()

    def test_get_affiliation_status_when_unaffiliated(self):
        """GET /api/riders/affiliation/ returns unaffiliated status."""
        self.client.force_authenticate(user=self.rider_user)
        response = self.client.get("/api/riders/affiliation/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["is_affiliated"] is False
        assert data["data"]["dispatcher"] is None

    def test_post_affiliation_with_invalid_code(self):
        """POST /api/riders/affiliation/ with invalid code returns 400."""
        self.client.force_authenticate(user=self.rider_user)
        response = self.client.post("/api/riders/affiliation/", {"affiliation_code": "INVALID99"}, format="json")
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "Invalid affiliation code" in data["message"]

    def test_post_affiliation_with_valid_code_success(self):
        """POST /api/riders/affiliation/ links rider to dispatcher."""
        self.client.force_authenticate(user=self.rider_user)
        response = self.client.post("/api/riders/affiliation/", {"affiliation_code": "hub123"}, format="json")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["is_affiliated"] is True
        assert data["data"]["dispatcher"]["affiliation_code"] == "HUB123"
        assert data["data"]["dispatcher"]["role"] == "Hub Captain"

        # Verify DB state
        self.rider.refresh_from_db()
        assert self.rider.is_affiliated is True
        assert self.rider.affiliated_to == self.dispatcher_profile
        assert self.rider.affiliated_at is not None

        # Verify count on dispatcher
        self.dispatcher_profile.refresh_from_db()
        assert self.dispatcher_profile.affiliated_riders_count == 1

    def test_post_affiliation_when_already_affiliated_fails(self):
        """POST /api/riders/affiliation/ when already affiliated returns 400."""
        self.client.force_authenticate(user=self.rider_user)
        self.client.post("/api/riders/affiliation/", {"affiliation_code": "HUB123"}, format="json")

        # Try linking again
        response = self.client.post("/api/riders/affiliation/", {"affiliation_code": "HUB123"}, format="json")
        assert response.status_code == 400
        data = response.json()
        assert "already affiliated" in data["message"]

    def test_rider_registration_serializer_with_affiliation_code(self):
        """Registering a new rider with affiliation_code associates rider to dispatcher."""
        from riders.serializers import RiderSelfRegistrationSerializer

        data = {
            "phone": "08091112233",
            "email": "newrider@example.com",
            "first_name": "Samuel",
            "last_name": "Rider",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "address": "123 Test Street, Ikeja",
            "emergency_contact_name": "Emergency Person",
            "emergency_phone": "08092223344",
            "bvn": "12345678901",
            "vehicle_model": "Bajaj Boxer",
            "vehicle_plate_number": "KJA-123-XY",
            "vehicle_color": "Red",
            "vehicle_photo": "https://example.com/bike.jpg",
            "rider_documents": [
                {"type": "drivers_license", "url": "https://example.com/dl.pdf"},
                {"type": "national_id", "url": "https://example.com/nin.pdf"},
                {"type": "profile_photo", "url": "https://example.com/photo.jpg"},
                {"type": "utility_bill", "url": "https://example.com/bill.pdf"},
                {"type": "riders_card", "url": "https://example.com/card.pdf"},
            ],
            "affiliation_code": "HUB123",
        }
        serializer = RiderSelfRegistrationSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        res = serializer.save()
        rider = res["rider"]
        assert rider.is_affiliated is True
        assert rider.affiliated_to == self.dispatcher_profile
        assert rider.affiliated_at is not None


@pytest.mark.django_db
class TestDispatcherAffiliationAPIs:

    @pytest.fixture(autouse=True)
    def setup_entities(self):
        self.client = APIClient()

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
        self.rider.is_affiliated = True
        self.rider.affiliated_to = self.dispatcher_profile
        self.rider.affiliated_at = timezone.now()
        self.rider.save()

        # Vehicle & Customer for orders
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
        self.customer = User.objects.create_user(
            phone="+2348055556666",
            password="password123",
            first_name="Alice",
            last_name="Merchant",
            usertype="Merchant",
        )

        # System settings
        self.settings = SystemSettings.objects.first()
        if not self.settings:
            self.settings = SystemSettings.objects.create(
                affiliation_commission_per_order=Decimal("3000.00")
            )
        else:
            self.settings.affiliation_commission_per_order = Decimal("3000.00")
            self.settings.save()

    def test_dispatcher_affiliation_summary(self):
        """GET /api/dispatch/affiliation/summary/ returns current dispatcher earnings and code."""
        self.client.force_authenticate(user=self.dispatcher_user)
        response = self.client.get("/api/dispatch/affiliation/summary/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        summary = data["data"]
        assert summary["affiliation_code"] == "HUB123"
        assert summary["affiliated_riders_count"] == 1
        assert Decimal(summary["monthly_commission"]) == Decimal("0.00")
        assert Decimal(summary["commission_per_order"]) == Decimal("3000.00")

    def test_dispatcher_affiliated_riders_list(self):
        """GET /api/dispatch/affiliation/riders/ returns list of linked riders."""
        self.client.force_authenticate(user=self.dispatcher_user)
        response = self.client.get("/api/dispatch/affiliation/riders/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        riders = data["data"]
        assert len(riders) == 1
        assert riders[0]["rider_id"] == "100001"
        assert riders[0]["is_affiliated"] is True

    def test_dispatcher_commissions_and_reconciliation_flow(self):
        """Test full commission flow: order completion, listing commissions, and reconciliation."""
        from dispatcher.services import record_dispatcher_affiliation_commission

        order = Order.objects.create(
            user=self.customer,
            rider=self.rider,
            vehicle=self.vehicle,
            order_number="ORD-API-01",
            status="Done",
            completed_at=timezone.now(),
            total_amount=Decimal("6000.00"),
        )
        record_dispatcher_affiliation_commission(order)

        self.client.force_authenticate(user=self.dispatcher_user)

        # 1. Summary should now show 3,000 commission
        summary_resp = self.client.get("/api/dispatch/affiliation/summary/")
        assert summary_resp.status_code == 200
        assert Decimal(summary_resp.json()["data"]["monthly_commission"]) == Decimal("3000.00")

        # 2. Commissions list should have 1 item
        comm_resp = self.client.get("/api/dispatch/affiliation/commissions/")
        assert comm_resp.status_code == 200
        comm_data = comm_resp.json()["data"]["results"]
        assert len(comm_data) == 1
        assert comm_data[0]["order_number"] == "ORD-API-01"
        assert Decimal(comm_data[0]["amount"]) == Decimal("3000.00")

        # 3. Monthly earnings list
        earn_resp = self.client.get("/api/dispatch/affiliation/monthly-earnings/")
        assert earn_resp.status_code == 200
        earnings = earn_resp.json()["data"]
        assert len(earnings) == 1
        assert earnings[0]["total_orders"] == 1
        assert Decimal(earnings[0]["total_commission"]) == Decimal("3000.00")

        # 4. Reconcile endpoint
        recon_resp = self.client.post("/api/dispatch/affiliation/reconcile/", {}, format="json")
        assert recon_resp.status_code == 200
        recon_data = recon_resp.json()["data"]
        assert recon_data["reconciled"] is True
        assert recon_data["total_orders"] == 1
        assert Decimal(recon_data["total_commission"]) == Decimal("3000.00")

    def test_unauthorized_user_cannot_access_dispatcher_affiliation(self):
        """Riders or normal users cannot access dispatcher affiliation endpoints."""
        self.client.force_authenticate(user=self.rider_user)
        response = self.client.get("/api/dispatch/affiliation/summary/")
        assert response.status_code == 403
