from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from orders.models import Order, Vehicle
from dispatcher.models import Zone, Rider, RelayNode
from riders.models import OrderOffer

User = get_user_model()


class UnverifiedRiderOfferRestrictionTests(TestCase):
    """
    Tests ensuring that unverified / unauthorized riders (especially independent
    riders pending KYC review) cannot view, accept, or receive order offers,
    nor go online on duty.
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Verified Rider
        self.verified_user = User.objects.create_user(
            phone="+2348111111111",
            email="verified@test.com",
            password="password123",
            usertype="Rider",
        )
        self.verified_rider = Rider.objects.get(user=self.verified_user)
        self.verified_rider.is_independent_rider = False
        self.verified_rider.is_authorized = True
        self.verified_rider.approval_status = Rider.ApprovalStatus.APPROVED
        self.verified_rider.save()

        # 2. Unverified Independent Rider (pending review)
        self.unverified_user = User.objects.create_user(
            phone="+2348222222222",
            email="unverified@test.com",
            password="password123",
            usertype="Rider",
        )
        self.unverified_rider = Rider.objects.get(user=self.unverified_user)
        self.unverified_rider.is_independent_rider = True
        self.unverified_rider.is_authorized = False
        self.unverified_rider.approval_status = Rider.ApprovalStatus.PENDING
        self.unverified_rider.save()

        # 3. Zone, Hub, Vehicle, and Order Setup
        self.zone = Zone.objects.create(
            name="Test Zone", center_lat=6.5244, center_lng=3.3792, is_active=True
        )
        self.hub = RelayNode.objects.create(
            name="Test Hub",
            address="Marina Hub Address",
            latitude=6.5244,
            longitude=3.3792,
            zone=self.zone,
        )
        self.verified_rider.hub = self.hub
        self.verified_rider.home_zone = self.zone
        self.verified_rider.save()

        # Refresh users to clear cached rider_profile
        self.verified_user.refresh_from_db()
        self.unverified_user.refresh_from_db()

        self.vehicle = Vehicle.objects.create(
            name="Motorcycle",
            max_weight_kg=50,
            base_price=500,
            base_fare=500,
            rate_per_km=50,
            rate_per_minute=5,
            is_active=True,
        )

        merchant_user = User.objects.create_user(
            phone="+2348333333333",
            email="merchant@test.com",
            password="password123",
            usertype="Merchant",
        )

        self.order = Order.objects.create(
            user=merchant_user,
            vehicle=self.vehicle,
            pickup_address="123 Marina St, Lagos",
            pickup_latitude=6.5244,
            pickup_longitude=3.3792,
            total_amount=Decimal("2000.00"),
            distance_km=Decimal("4.5"),
            duration_minutes=15,
            status="Pending",
        )

        self.offer, _ = OrderOffer.objects.get_or_create(
            order=self.order,
            defaults={
                "status": "pending",
                "zone": self.zone,
                "estimated_earnings": Decimal("400.00"),
            },
        )
        self.offer.status = "pending"
        self.offer.zone = self.zone
        self.offer.save()

    def test_unverified_independent_rider_cannot_list_order_offers(self):
        """Unverified rider receives 403 Forbidden when calling order offers list."""
        self.client.force_authenticate(user=self.unverified_user)
        response = self.client.get("/api/riders/orders/offers/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_verified_rider_can_list_order_offers(self):
        """Verified authorized rider receives 200 OK with available offers."""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.get("/api/riders/orders/offers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        offer_ids = [o["id"] for o in response.data]
        self.assertIn(str(self.offer.id), offer_ids)

    def test_unverified_independent_rider_cannot_accept_order_offer(self):
        """Unverified rider receives 403 Forbidden when attempting to accept an offer."""
        self.client.force_authenticate(user=self.unverified_user)
        response = self.client.post(
            f"/api/riders/orders/offers/{self.offer.id}/accept/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, "pending")

    def test_verified_rider_can_accept_order_offer(self):
        """Verified authorized rider in valid zone can accept an offer."""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(
            f"/api/riders/orders/offers/{self.offer.id}/accept/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, "accepted")
        self.assertEqual(self.offer.rider, self.verified_rider)

    def test_unverified_independent_rider_cannot_toggle_online(self):
        """Unverified rider cannot toggle duty status to online."""
        self.client.force_authenticate(user=self.unverified_user)
        response = self.client.post(
            "/api/riders/duty/",
            {"status": "online", "latitude": 6.5244, "longitude": 3.3792},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.unverified_rider.refresh_from_db()
        self.assertEqual(self.unverified_rider.status, Rider.Status.OFFLINE)

    def test_verified_rider_can_toggle_online(self):
        """Verified authorized rider can toggle duty status to online."""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(
            "/api/riders/duty/",
            {"status": "online", "latitude": 6.5244, "longitude": 3.3792},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.verified_rider.refresh_from_db()
        self.assertEqual(self.verified_rider.status, Rider.Status.ONLINE)
