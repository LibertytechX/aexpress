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
        self.rider_a.save()

        self.rider_b = Rider.objects.get(user=self.user_b)
        self.rider_b.home_zone = self.zone_b
        self.rider_b.save()

        # Refresh users to clear cached rider_profile
        self.user_a.refresh_from_db()
        self.user_b.refresh_from_db()
        self.user_no_zone.refresh_from_db()

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
            total_amount=Decimal("1000.00"),
            distance_km=Decimal("5.0"),
            duration_minutes=15,
        )
        self.offer_a = OrderOffer.objects.create(
            order=order1,
            status="pending",
            zone=self.zone_a,
            estimated_earnings=Decimal("200.00"),
        )

        order2 = Order.objects.create(
            user=self.user_a,
            vehicle=self.vehicle,
            pickup_address="Address B",
            total_amount=Decimal("1500.00"),
            distance_km=Decimal("8.0"),
            duration_minutes=20,
        )
        self.offer_b = OrderOffer.objects.create(
            order=order2,
            status="pending",
            zone=self.zone_b,
            estimated_earnings=Decimal("300.00"),
        )

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
