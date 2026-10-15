import pytest
from rest_framework.test import APIClient
from rest_framework import status

from authentication.models import User
from dispatcher.models import DispatcherProfile, RelayNode, Zone


@pytest.mark.django_db
class TestVerifyAffiliationCodeAPI:

    @pytest.fixture(autouse=True)
    def setup_entities(self):
        self.client = APIClient()

        # Create active Hub Captain dispatcher
        self.hub_captain_user = User.objects.create_user(
            phone="+2348011110001",
            password="password123",
            first_name="Alice",
            last_name="Captain",
            contact_name="Alice Hub Captain",
            usertype="Dispatcher",
        )
        self.hub_captain_profile = DispatcherProfile.objects.get(user=self.hub_captain_user)
        self.hub_captain_profile.affiliation_code = "HUB001"
        self.hub_captain_profile.role = DispatcherProfile.Role.HUB_CAPTAIN
        self.hub_captain_profile.save()

        # Create RelayNode & Zone linked to Hub Captain
        self.zone = Zone.objects.create(
            name="Ikeja Zone",
            center_lat=6.5925,
            center_lng=3.3547,
            radius_km=5.0,
        )
        self.relay_node = RelayNode.objects.create(
            name="Ikeja Central Hub",
            address="10 Allen Avenue, Ikeja",
            latitude=6.5925,
            longitude=3.3547,
            hub_captain_name="Alice Captain",
            hub_captain_phone="+2348011110001",
            zone=self.zone,
        )

        # Create Zone Lead dispatcher
        self.zone_lead_user = User.objects.create_user(
            phone="+2348011110002",
            password="password123",
            first_name="Bob",
            last_name="Lead",
            contact_name="Bob Zone Lead",
            usertype="Dispatcher",
        )
        self.zone_lead_profile = DispatcherProfile.objects.get(user=self.zone_lead_user)
        self.zone_lead_profile.affiliation_code = "ZONE002"
        self.zone_lead_profile.role = DispatcherProfile.Role.ZONE_LEAD
        self.zone_lead_profile.save()

        # Create Admin dispatcher (non-affiliate role)
        self.admin_user = User.objects.create_user(
            phone="+2348011110003",
            password="password123",
            first_name="Charlie",
            last_name="Admin",
            usertype="Dispatcher",
        )
        self.admin_profile = DispatcherProfile.objects.get(user=self.admin_user)
        self.admin_profile.affiliation_code = "ADM003"
        self.admin_profile.role = DispatcherProfile.Role.ADMIN
        self.admin_profile.save()

        # Create Inactive dispatcher
        self.inactive_user = User.objects.create_user(
            phone="+2348011110004",
            password="password123",
            first_name="Inactive",
            last_name="Captain",
            usertype="Dispatcher",
            is_active=False,
        )
        self.inactive_profile = DispatcherProfile.objects.get(user=self.inactive_user)
        self.inactive_profile.affiliation_code = "INACT004"
        self.inactive_profile.role = DispatcherProfile.Role.HUB_CAPTAIN
        self.inactive_profile.save()

    def test_verify_code_get_success_hub_captain(self):
        """Test GET /api/auth/affiliation/verify/?code=HUB001 returns dispatcher and hub details."""
        response = self.client.get("/api/auth/affiliation/verify/?code=HUB001")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        res_data = data["data"]
        assert res_data["is_valid"] is True
        assert res_data["affiliation_code"] == "HUB001"
        assert res_data["name"] == "Alice Hub Captain"
        assert res_data["phone"] == "+2348011110001"
        assert res_data["role"] == "hub_captain"
        assert res_data["role_display"] == "Hub Captain"
        assert res_data["hub_name"] == "Ikeja Central Hub"
        assert res_data["zone_name"] == "Ikeja Zone"

    def test_verify_code_get_case_insensitive_and_whitespace(self):
        """Test code lookup handles lowercase and surrounding whitespace."""
        response = self.client.get("/api/auth/affiliation/verify/?code=  hub001  ")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["affiliation_code"] == "HUB001"

    def test_verify_code_get_using_affiliation_code_param(self):
        """Test GET using ?affiliation_code=... instead of ?code=..."""
        response = self.client.get("/api/auth/affiliation/verify/?affiliation_code=ZONE002")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["affiliation_code"] == "ZONE002"
        assert data["data"]["role"] == "zone_lead"

    def test_verify_code_post_success(self):
        """Test POST /api/auth/affiliation/verify/ with JSON payload."""
        response = self.client.post(
            "/api/auth/affiliation/verify/",
            {"affiliation_code": "HUB001"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["affiliation_code"] == "HUB001"

    def test_verify_code_post_using_code_alias(self):
        """Test POST with {'code': 'ZONE002'} alias."""
        response = self.client.post(
            "/api/auth/affiliation/verify/",
            {"code": "zone002"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["affiliation_code"] == "ZONE002"

    def test_verify_code_empty_code_returns_400(self):
        """Test empty code raises validation error."""
        response = self.client.get("/api/auth/affiliation/verify/?code=")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Affiliation code is required" in data["message"]

    def test_verify_code_missing_param_returns_400(self):
        """Test missing parameter raises validation error."""
        response = self.client.get("/api/auth/affiliation/verify/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Affiliation code is required" in data["message"]

    def test_verify_code_non_existent_code_returns_400(self):
        """Test nonexistent code returns 400 with descriptive error."""
        response = self.client.get("/api/auth/affiliation/verify/?code=NONEXISTENT999")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid affiliation code" in data["message"]

    def test_verify_code_admin_role_returns_400(self):
        """Test affiliation code belonging to Admin returns 400."""
        response = self.client.get("/api/auth/affiliation/verify/?code=ADM003")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "does not belong to an active Hub Captain or Zone Lead" in data["message"]

    def test_verify_code_inactive_account_returns_400(self):
        """Test code belonging to inactive user returns 400."""
        response = self.client.get("/api/auth/affiliation/verify/?code=INACT004")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "inactive account" in data["message"]

    def test_verify_code_accessible_on_all_alias_routes(self):
        """Verify the endpoint is accessible on all configured routes without auth."""
        routes = [
            "/api/auth/affiliation/verify/?code=HUB001",
            "/api/merchant/affiliation/verify/?code=HUB001",
            "/api/affiliation/verify/?code=HUB001",
            "/api/riders/affiliation/verify/?code=HUB001",
        ]
        for route in routes:
            response = self.client.get(route)
            assert response.status_code == status.HTTP_200_OK, f"Failed on route {route}"
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["affiliation_code"] == "HUB001"
