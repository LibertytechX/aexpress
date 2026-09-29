import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.utils import timezone

from authentication.models import User
from dispatcher.models import RelayNode, Rider, Zone
from orders.models import Order, Vehicle
from riders.leaderboard_service import LeaderboardService
from riders.models import LeaderboardEntry, RiderEarning


@pytest.mark.django_db
class TestLeaderboardService:
    def setup_method(self):
        self.user = User.objects.create_user(
            phone="08011112222",
            password="password123",
            first_name="Leaderboard",
            last_name="Merchant",
        )
        self.rider_user1 = User.objects.create_user(
            phone="08033334444",
            password="password123",
            first_name="Rider",
            last_name="One",
        )
        self.rider_user2 = User.objects.create_user(
            phone="08055556666",
            password="password123",
            first_name="Rider",
            last_name="Two",
        )
        self.zone = Zone.objects.create(
            name="Lekki Phase 1", center_lat=6.4474, center_lng=3.4723
        )
        self.hub = RelayNode.objects.create(
            name="Lekki Hub",
            address="Lekki Phase 1",
            latitude=6.4474,
            longitude=3.4723,
            zone=self.zone,
        )
        self.rider1 = Rider.objects.create(
            user=self.rider_user1, rider_id="R-001", status="online", hub=self.hub
        )
        self.rider2 = Rider.objects.create(
            user=self.rider_user2, rider_id="R-002", status="online", hub=self.hub
        )
        self.vehicle = Vehicle.objects.create(
            name="Motorbike",
            max_weight_kg=20,
            base_price=500,
            base_fare=500,
            rate_per_km=100,
            rate_per_minute=10,
            min_distance_km=2,
            min_fee=1000,
        )

    def test_get_period_tuples(self):
        today = timezone.now().date()
        periods = LeaderboardService.get_period_tuples(today)
        assert len(periods) == 3

        week_type, week_key, week_filter = periods[0]
        assert week_type == LeaderboardEntry.PeriodType.THIS_WEEK
        assert week_key == today.strftime("%Y-W%W")
        assert "completed_at__date__gte" in week_filter

        month_type, month_key, month_filter = periods[1]
        assert month_type == LeaderboardEntry.PeriodType.THIS_MONTH
        assert month_key == today.strftime("%Y-%m")
        assert "completed_at__date__gte" in month_filter

        all_type, all_key, all_filter = periods[2]
        assert all_type == LeaderboardEntry.PeriodType.ALL_TIME
        assert all_key == "all_time"
        assert all_filter == {}

    def test_record_order_completion_db_and_redis(self):
        now = timezone.now()
        order = Order.objects.create(
            order_number="ORD-LB-01",
            user=self.user,
            rider=self.rider1,
            vehicle=self.vehicle,
            status="Done",
            completed_at=now,
            pickup_address="Lekki",
            total_amount=3000,
            distance_km=10,
        )
        RiderEarning.objects.create(
            rider=self.rider1,
            order=order,
            base_fare=3000,
            net_earning=600,
        )

        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe

        with patch.object(LeaderboardService, "get_redis_client", return_value=mock_redis):
            LeaderboardService.record_order_completion(order)

        # Verify Redis pipeline called
        assert mock_pipe.zincrby.called
        assert mock_pipe.execute.called

        # Verify DB LeaderboardEntry updated
        today = now.date()
        month_key = today.strftime("%Y-%m")
        entry = LeaderboardEntry.objects.get(
            rider=self.rider1,
            period_type=LeaderboardEntry.PeriodType.THIS_MONTH,
            period_key=month_key,
        )
        assert entry.trips_count == 1
        assert entry.earnings == Decimal("600.00")
        assert entry.zone_name == "Lekki Phase 1"

    def test_get_leaderboard_from_db_fallback(self):
        today = timezone.now().date()
        month_key = today.strftime("%Y-%m")

        LeaderboardEntry.objects.create(
            rider=self.rider1,
            period_type=LeaderboardEntry.PeriodType.THIS_MONTH,
            period_key=month_key,
            rank=1,
            trips_count=15,
            earnings=Decimal("9000.00"),
            zone_name="Lekki Phase 1",
        )
        LeaderboardEntry.objects.create(
            rider=self.rider2,
            period_type=LeaderboardEntry.PeriodType.THIS_MONTH,
            period_key=month_key,
            rank=2,
            trips_count=10,
            earnings=Decimal("6000.00"),
            zone_name="Lekki Phase 1",
        )

        with patch.object(LeaderboardService, "get_redis_client", return_value=None):
            result = LeaderboardService.get_leaderboard(
                period_type=LeaderboardEntry.PeriodType.THIS_MONTH,
                period_key=month_key,
                current_rider=self.rider1,
            )

        assert result["period"] == LeaderboardEntry.PeriodType.THIS_MONTH
        assert result["my_rank"] == 1
        assert len(result["entries"]) == 2
        assert result["entries"][0]["rider_id"] == "R-001"
        assert result["entries"][0]["is_me"] is True
        assert result["entries"][1]["rider_id"] == "R-002"
        assert result["entries"][1]["is_me"] is False

    def test_get_rider_rank(self):
        today = timezone.now().date()
        month_key = today.strftime("%Y-%m")

        mock_redis = MagicMock()
        mock_redis.zrevrank.return_value = 0  # 0-indexed rank -> 1st place

        with patch.object(LeaderboardService, "get_redis_client", return_value=mock_redis):
            rank = LeaderboardService.get_rider_rank(
                self.rider1.id,
                LeaderboardEntry.PeriodType.THIS_MONTH,
                month_key,
            )
            assert rank == 1

        # Fallback to DB when Redis returns None
        LeaderboardEntry.objects.create(
            rider=self.rider2,
            period_type=LeaderboardEntry.PeriodType.THIS_MONTH,
            period_key=month_key,
            rank=5,
            trips_count=7,
            earnings=Decimal("4000.00"),
        )
        with patch.object(LeaderboardService, "get_redis_client", return_value=None):
            rank = LeaderboardService.get_rider_rank(
                self.rider2.id,
                LeaderboardEntry.PeriodType.THIS_MONTH,
                month_key,
            )
            assert rank == 5
