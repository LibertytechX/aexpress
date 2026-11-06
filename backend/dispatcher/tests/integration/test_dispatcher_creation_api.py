import pytest
from rest_framework import status
from rest_framework.test import APIClient
from authentication.models import User
from dispatcher.models import DispatcherProfile


@pytest.mark.django_db
class TestDispatcherCreationAPI:
    @pytest.fixture(autouse=True)
    def setup_client(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            phone="+2348010000001",
            password="adminpassword123",
            first_name="Admin",
            last_name="User",
            usertype="Dispatcher",
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_create_dispatcher_success_admin_role(self):
        payload = {
            "first_name": "Samuel",
            "last_name": "Dispatcher",
            "phone": "+2348010000002",
            "email": "samuel.dispatcher@example.com",
            "password": "strongpassword123",
            "role": "admin",
        }
        response = self.client.post("/api/dispatch/dispatchers/", data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["name"] == "Samuel Dispatcher"
        assert response.data["phone"] == "+2348010000002"
        assert response.data["email"] == "samuel.dispatcher@example.com"
        assert response.data["role"] == "Admin"
        assert DispatcherProfile.objects.filter(user__phone="+2348010000002").count() == 1

    def test_create_dispatcher_success_hub_captain_role(self):
        payload = {
            "first_name": "Fola",
            "last_name": "Captain",
            "phone": "+2348010000003",
            "email": "fola.captain@example.com",
            "password": "strongpassword123",
            "role": "hub_captain",
        }
        response = self.client.post("/api/dispatch/dispatchers/", data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["name"] == "Fola Captain"
        assert response.data["role"] == "Hub Captain"
        assert response.data["affiliation_code"] is not None
        assert len(response.data["affiliation_code"]) > 0

    def test_create_dispatcher_success_zone_lead_role(self):
        payload = {
            "first_name": "Tunde",
            "last_name": "Lead",
            "phone": "+2348010000004",
            "email": "tunde.lead@example.com",
            "password": "strongpassword123",
            "role": "zone_lead",
        }
        response = self.client.post("/api/dispatch/dispatchers/", data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["name"] == "Tunde Lead"
        assert response.data["role"] == "Zone Lead"
        assert response.data["affiliation_code"] is not None
        assert len(response.data["affiliation_code"]) > 0

    def test_list_dispatchers_includes_created_dispatcher(self):
        payload = {
            "first_name": "Listed",
            "last_name": "Dispatcher",
            "phone": "+2348010000005",
            "email": "listed.dispatcher@example.com",
            "password": "strongpassword123",
            "role": "admin",
        }
        create_res = self.client.post("/api/dispatch/dispatchers/", data=payload, format="json")
        assert create_res.status_code == status.HTTP_201_CREATED

        list_res = self.client.get("/api/dispatch/dispatchers/")
        assert list_res.status_code == status.HTTP_200_OK
        phones = [d["phone"] for d in list_res.data]
        assert "+2348010000005" in phones

    def test_create_dispatcher_unauthenticated_forbidden(self):
        self.client.force_authenticate(user=None)
        payload = {
            "first_name": "Unauth",
            "last_name": "User",
            "phone": "+2348010000006",
            "email": "unauth@example.com",
            "password": "strongpassword123",
        }
        response = self.client.post("/api/dispatch/dispatchers/", data=payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
