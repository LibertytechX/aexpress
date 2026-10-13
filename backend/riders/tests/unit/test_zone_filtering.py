from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from orders.models import Order, Vehicle
from dispatcher.models import Zone, Rider
from riders.models import OrderOffer

User = get_user_model()


class ZoneFilteringTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(
            phone="+2348123456789",
            email="ridera@test.com",
            password="password123",
            usertype="Rider",
        )
        self.user_b = User.objects.create_user(
            phone="+2348123456780",
            email="riderb@test.com",
            password="password123",
            usertype="Rider",
        )
        self.user_no_zone = User.objects.create_user(
            phone="+2348123456781",
            email="riderno@test.com",
            password="password123",
            usertype="Rider",
        )

        self.zone_a = Zone.objects.create(
            name="Zone A", center_lat=6.6059, center_lng=3.3491, is_active=True
        )
        self.zone_b = Zone.objects.create(
            name="Zone B", center_lat=6.4531, center_lng=3.3958, is_active=True
        )

        # Rider profiles are created via signals (presumably) but let's ensure they exist
        self.rider_a = Rider.objects.get(user=self.user_a)
        self.rider_a.home_zone = self.zone_a
        self.rider_a.is_authorized = True
        self.rider_a.approval_status = Rider.ApprovalStatus.APPROVED
        self.rider_a.save()

        self.rider_b = Rider.objects.get(user=self.user_b)
        self.rider_b.home_zone = self.zone_b
        self.rider_b.is_authorized = True
        self.rider_b.approval_status = Rider.ApprovalStatus.APPROVED
        self.rider_b.save()

        self.rider_no_zone = Rider.objects.get(user=self.user_no_zone)
        self.rider_no_zone.is_authorized = True
        self.rider_no_zone.approval_status = Rider.ApprovalStatus.APPROVED
        self.rider_no_zone.save()

        # Unverified independent rider
        self.user_unverified = User.objects.create_user(
            phone="+2348123456782",
            email="unverified@test.com",
            password="password123",
            usertype="Rider",
        )
        self.rider_unverified = Rider.objects.get(user=self.user_unverified)
        self.rider_unverified.is_independent_rider = True
        self.rider_unverified.is_authorized = False
        self.rider_unverified.approval_status = Rider.ApprovalStatus.PENDING
        self.rider_unverified.save()

        # Refresh users to clear cached rider_profile
        self.user_a.refresh_from_db()
        self.user_b.refresh_from_db()
        self.user_no_zone.refresh_from_db()
        self.user_unverified.refresh_from_db()

        self.vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=100,
            base_price=500,
            base_fare=500,
            rate_per_km=50,
            rate_per_minute=5,
            is_active=True,
        )

        # Create orders and offers
        order1 = Order.objects.create(
            user=self.user_a,  # Merchant in real case but here just for owner
            vehicle=self.vehicle,
            pickup_address="Address A",
            pickup_latitude=6.6059,
            pickup_longitude=3.3491,
            total_amount=Decimal("1000.00"),
            distance_km=Decimal("5.0"),
            duration_minutes=15,
        )
        self.offer_a, _ = OrderOffer.objects.get_or_create(
            order=order1,
            defaults={
                "status": "pending",
                "zone": self.zone_a,
                "estimated_earnings": Decimal("200.00"),
            },
        )
        self.offer_a.status = "pending"
        self.offer_a.zone = self.zone_a
        self.offer_a.save()

        order2 = Order.objects.create(
            user=self.user_a,
            vehicle=self.vehicle,
            pickup_address="Address B",
            pickup_latitude=6.4531,
            pickup_longitude=3.3958,
            total_amount=Decimal("1500.00"),
            distance_km=Decimal("8.0"),
            duration_minutes=20,
        )
        self.offer_b, _ = OrderOffer.objects.get_or_create(
            order=order2,
            defaults={
                "status": "pending",
                "zone": self.zone_b,
                "estimated_earnings": Decimal("300.00"),
            },
        )
        self.offer_b.status = "pending"
        self.offer_b.zone = self.zone_b
        self.offer_b.save()

    def test_rider_a_sees_only_zone_a_offers(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get("/api/riders/orders/offers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [offer["id"] for offer in response.data]
        self.assertIn(str(self.offer_a.id), ids)
        self.assertNotIn(str(self.offer_b.id), ids)

    def test_rider_b_sees_only_zone_b_offers(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get("/api/riders/orders/offers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [offer["id"] for offer in response.data]
        self.assertNotIn(str(self.offer_a.id), ids)
        self.assertIn(str(self.offer_b.id), ids)

    def test_rider_no_zone_sees_all_offers(self):
        self.client.force_authenticate(user=self.user_no_zone)
        response = self.client.get("/api/riders/orders/offers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [offer["id"] for offer in response.data]
        self.assertIn(str(self.offer_a.id), ids)
        self.assertIn(str(self.offer_b.id), ids)

    def test_unverified_independent_rider_cannot_see_offers(self):
        self.client.force_authenticate(user=self.user_unverified)
        response = self.client.get("/api/riders/orders/offers/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rider_a_can_accept_zone_a_offer(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            f"/api/riders/orders/offers/{self.offer_a.id}/accept/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer_a.refresh_from_db()
        self.assertEqual(self.offer_a.status, "accepted")
        self.assertEqual(self.offer_a.rider, self.rider_a)

    def test_rider_a_cannot_accept_zone_b_offer(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            f"/api/riders/orders/offers/{self.offer_b.id}/accept/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["message"], "Rider is not in the zone.")
        self.offer_b.refresh_from_db()
        self.assertEqual(self.offer_b.status, "pending")

    def test_rider_no_zone_cannot_accept_zoned_offer(self):
        self.client.force_authenticate(user=self.user_no_zone)
        response = self.client.post(
            f"/api/riders/orders/offers/{self.offer_a.id}/accept/"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("hub or home zone", response.data["message"])

