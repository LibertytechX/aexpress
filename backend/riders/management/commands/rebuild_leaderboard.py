"""
rebuild_leaderboard — management command
Rebuilds the leaderboard snapshot for all three periods:
  - this_week
  - this_month
  - all_time

Run nightly via cron:
  python manage.py rebuild_leaderboard
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Sum
from decimal import Decimal

from dispatcher.models import Rider
from orders.models import Order
from riders.models import LeaderboardEntry, RiderEarning
from riders.leaderboard_service import LeaderboardService


class Command(BaseCommand):
    help = "Rebuilds the leaderboard snapshot for this_week, this_month, and all_time in DB and Redis."

    def handle(self, *args, **options):
        today = timezone.now().date()
        self.stdout.write("🏆 Rebuilding leaderboard...")

        for period_type, period_key, date_filter in LeaderboardService.get_period_tuples(today):
            self._rebuild_period(period_type, period_key, date_filter)

        self.stdout.write(self.style.SUCCESS("✅ Leaderboard rebuilt successfully."))

    def _rebuild_period(self, period_type, period_key, date_filter):
        self.stdout.write(f"  → {period_type} ({period_key})")

        # Get all riders with at least one completed order in the period
        order_qs = Order.objects.filter(
            status="Done", rider__isnull=False, **date_filter
        )

        # Aggregate trips and earnings per rider
        rider_stats = (
            order_qs.values("rider")
            .annotate(
                trips_count=Count("id"),
                earnings=Sum("rider_earning__net_earning"),
            )
            .order_by("-trips_count")
        )

        # Wipe and rewrite the period entries
        LeaderboardEntry.objects.filter(
            period_type=period_type, period_key=period_key
        ).delete()

        entries = []
        for rank, stat in enumerate(rider_stats, start=1):
            try:
                rider = Rider.objects.get(id=stat["rider"])
            except Rider.DoesNotExist:
                continue

            zone_name = rider.hub.zone.name if rider.hub and rider.hub.zone else ""
            entries.append(
                LeaderboardEntry(
                    rider=rider,
                    period_type=period_type,
                    period_key=period_key,
                    rank=rank,
                    trips_count=stat["trips_count"] or 0,
                    earnings=stat["earnings"] or Decimal("0.00"),
                    zone_name=zone_name,
                )
            )

        created_entries = LeaderboardEntry.objects.bulk_create(entries)
        # Warm Redis Sorted Sets with the fresh ranking snapshot
        LeaderboardService.warm_redis_for_period(
            period_type=period_type,
            period_key=period_key,
            entries=created_entries,
        )
        self.stdout.write(f"     {len(entries)} riders ranked and synced to Redis.")
