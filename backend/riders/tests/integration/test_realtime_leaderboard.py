import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from authentication.models import User
from dispatcher.models import RelayNode, Rider, Zone
from orders.models import Order, Vehicle
from orders.tasks import handle_order_completion_tasks
from riders.models import LeaderboardEntry, RiderEarning


@pytest.mark.django_db
class TestRealtimeLeaderboardIntegration:
    def setup_method(self):
        self.client = APIClient()
        self.merchant_user = User.objects.create_user(
            phone="08099990001",
            password="password123",
            first_name="Leaderboard",
            last_name="Merchant",
        )
        self.rider_user = User.objects.create_user(
            phone="08099990002",
            password="password123",
            first_name="Speedy",
            last_name="Rider",
            contact_name="Speedy Rider",
        )
        self.zone = Zone.objects.create(
            name="Victoria Island", center_lat=6.4281, center_lng=3.4219
        )
        self.hub = RelayNode.objects.create(
            name="VI Hub",
            address="Victoria Island",
            latitude=6.4281,
            longitude=3.4219,
            zone=self.zone,
        )
        self.rider = Rider.objects.create(
            user=self.rider_user, rider_id="R-01", status="online", hub=self.hub
        )
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
        self.client.force_authenticate(user=self.rider_user)

    def test_order_completion_updates_leaderboard(self):
        now = timezone.now()
        order = Order.objects.create(
            order_number="ORD-RT-100",
            user=self.merchant_user,
            rider=self.rider,
            vehicle=self.vehicle,
            status="Done",
            completed_at=now,
            pickup_address="VI Lagos",
            total_amount=5000,
            distance_km=8,
        )
        RiderEarning.objects.create(
            rider=self.rider,
            order=order,
            base_fare=5000,
            net_earning=1000,
        )

        # Trigger handle_order_completion_tasks
        res = handle_order_completion_tasks(str(order.id))
        assert res is True

        today = now.date()
        month_key = today.strftime("%Y-%m")

        entry = LeaderboardEntry.objects.filter(
            rider=self.rider,
            period_type=LeaderboardEntry.PeriodType.THIS_MONTH,
            period_key=month_key,
        ).first()

        assert entry is not None
        assert entry.trips_count == 1
        assert entry.earnings == Decimal("1000.00")
        assert entry.zone_name == "Victoria Island"

    def test_leaderboard_endpoint_returns_realtime_data(self):
        today = timezone.now().date()
        month_key = today.strftime("%Y-%m")

        LeaderboardEntry.objects.create(
            rider=self.rider,
            period_type=LeaderboardEntry.PeriodType.THIS_MONTH,
            period_key=month_key,
            rank=1,
            trips_count=5,
            earnings=Decimal("5000.00"),
            zone_name="Victoria Island",
        )

        response = self.client.get("/api/riders/leaderboard/?period=this_month")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["period"] == "this_month"
        assert data["period_key"] == month_key
        assert data["my_rank"] == 1
        assert len(data["entries"]) >= 1
        assert data["entries"][0]["rider_id"] == "R-01"
        assert data["entries"][0]["trips_count"] == 5
        assert data["entries"][0]["is_me"] is True

    def test_rebuild_leaderboard_command_syncs_redis_and_db(self):
        now = timezone.now()
        order = Order.objects.create(
            order_number="ORD-RT-200",
            user=self.merchant_user,
            rider=self.rider,
            vehicle=self.vehicle,
            status="Done",
            completed_at=now,
            pickup_address="VI Lagos",
            total_amount=4000,
            distance_km=5,
        )
        RiderEarning.objects.create(
            rider=self.rider,
            order=order,
            base_fare=4000,
            net_earning=800,
        )

        with patch("riders.leaderboard_service.LeaderboardService.warm_redis_for_period") as mock_warm:
            call_command("rebuild_leaderboard")
            assert mock_warm.called

        today = now.date()
        month_key = today.strftime("%Y-%m")
        entry = LeaderboardEntry.objects.filter(
            rider=self.rider,
            period_type=LeaderboardEntry.PeriodType.THIS_MONTH,
            period_key=month_key,
        ).first()

        assert entry is not None
        assert entry.rank == 1
        assert entry.trips_count == 1
        assert entry.earnings == Decimal("800.00")
