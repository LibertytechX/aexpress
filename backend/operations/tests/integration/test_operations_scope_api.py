"""Integration tests for Operations scope, zones, KM integrity, and admin console API endpoints."""

from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient

from authentication.models import User
from dispatcher.models import (
    DispatcherProfile,
    RelayNode,
    VehicleAsset,
    Vertical,
    Zone,
    ZoneCaptain,
)


class OperationsScopeApiTests(TestCase):
    """Integration tests for operations scope and zone access control."""

    def setUp(self):
        self.client = APIClient()
        self.vertical_a = Vertical.objects.create(
            name="Island / Lekki",
            code="A",
            lead_name="Lead A",
        )
        self.vertical_b = Vertical.objects.create(
            name="Mainland",
            code="B",
            lead_name="Lead B",
        )
        self.zone_a = Zone.objects.create(
            vertical=self.vertical_a,
            name="Ajah",
            center_lat=6.4698,
            center_lng=3.5852,
            radius_km=5,
        )
        self.zone_b = Zone.objects.create(
            vertical=self.vertical_b,
            name="Yaba",
            center_lat=6.5244,
            center_lng=3.3792,
            radius_km=5,
        )
        self.hub_a = RelayNode.objects.create(
            name="NG-AJAH-STATION",
            address="Ajah",
            latitude=6.4698,
            longitude=3.5852,
            zone=self.zone_a,
        )
        self.hub_b = RelayNode.objects.create(
            name="NG-YABA-STATION",
            address="Yaba",
            latitude=6.5244,
            longitude=3.3792,
            zone=self.zone_b,
        )

        self.admin = User.objects.create_user(
            phone="08000000001",
            email="ops-admin@example.com",
            password="password",
            usertype="Dispatcher",
            contact_name="Ops Admin",
        )
        self.captain_user = User.objects.create_user(
            phone="08000000002",
            email="zone-captain@example.com",
            password="password",
            usertype="ZoneCaptain",
            contact_name="Zone Captain",
        )
        ZoneCaptain.objects.create(user=self.captain_user, zone=self.zone_a)

    def test_admin_can_see_all_zones(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/operations/v1/zones/")

        self.assertEqual(response.status_code, 200)
        zone_names = {row["name"] for row in response.data["results"]}
        self.assertEqual(zone_names, {"Ajah", "Yaba"})

    def test_zone_captain_only_sees_assigned_zone(self):
        self.client.force_authenticate(user=self.captain_user)

        response = self.client.get("/api/operations/v1/zones/")

        self.assertEqual(response.status_code, 200)
        zone_names = [row["name"] for row in response.data["results"]]
        self.assertEqual(zone_names, ["Ajah"])

    def test_zone_captain_cannot_access_other_zone_detail(self):
        self.client.force_authenticate(user=self.captain_user)

        response = self.client.get(f"/api/operations/v1/zones/{self.zone_b.id}/")

        self.assertEqual(response.status_code, 403)


class OperationsKmIntegrityTests(TestCase):
    """Integration tests for KM integrity endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            phone="08000000003",
            email="km-admin@example.com",
            password="password",
            usertype="Dispatcher",
            contact_name="KM Admin",
        )

    def test_km_integrity_endpoint_filters_by_status(self):
        VehicleAsset.objects.create(
            plate_number="KM-PASS-001",
            distance_today=Decimal("100.00"),
            deliveries_km_today=Decimal("95.00"),
        )
        VehicleAsset.objects.create(
            plate_number="KM-FAIL-001",
            distance_today=Decimal("100.00"),
            deliveries_km_today=Decimal("80.00"),
        )
        VehicleAsset.objects.create(
            plate_number="KM-UNAVAILABLE-001",
            distance_today=None,
            deliveries_km_today=Decimal("0.00"),
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/operations/v1/km-integrity/?status=failed")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["plate_number"], "KM-FAIL-001")


class OperationsAdminConsoleTests(TestCase):
    """Integration tests for operations admin console zone management."""

    def setUp(self):
        self.client = APIClient()
        self.vertical = Vertical.objects.create(
            name="Island / Lekki",
            code="A",
            lead_name="Lead A",
        )
        self.admin = User.objects.create_user(
            phone="08000000004",
            email="admin-console@example.com",
            password="password",
            usertype="Dispatcher",
            contact_name="Admin Console",
        )
        self.viewer = User.objects.create_user(
            phone="08000000005",
            email="viewer@example.com",
            password="password",
            usertype="ZoneCaptain",
            contact_name="Viewer",
        )

    def test_non_admin_cannot_create_zone(self):
        self.client.force_authenticate(user=self.viewer)

        response = self.client.post(
            "/api/operations/v1/admin/zones/",
            {
                "name": "Unauthorized Zone",
                "vertical": str(self.vertical.id),
                "center_lat": 6.5,
                "center_lng": 3.4,
                "radius_km": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_dispatcher_admin_can_create_zone(self):
        DispatcherProfile.objects.filter(user=self.admin).update(role="admin")
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/operations/v1/admin/zones/",
            {
                "name": "Authorized Zone",
                "vertical": str(self.vertical.id),
                "center_lat": 6.5,
                "center_lng": 3.4,
                "radius_km": 5,
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Authorized Zone")
