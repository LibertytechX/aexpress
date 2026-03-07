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


class Command(BaseCommand):
    help = "Rebuilds the leaderboard snapshot for this_week, this_month, and all_time."

    def handle(self, *args, **options):
        today = timezone.now().date()
        self.stdout.write("🏆 Rebuilding leaderboard...")

        for period_type, period_key, date_filter in self._get_periods(today):
            self._rebuild_period(period_type, period_key, date_filter)

        self.stdout.write(self.style.SUCCESS("✅ Leaderboard rebuilt successfully."))

    def _get_periods(self, today):
        from datetime import timedelta

        # This week (Mon – today)
        week_start = today - timedelta(days=today.weekday())
        week_key = today.strftime("%Y-W%W")

        # This month
        month_start = today.replace(day=1)
        month_key = today.strftime("%Y-%m")

        return [
            (
                LeaderboardEntry.PeriodType.THIS_WEEK,
                week_key,
                {
                    "completed_at__date__gte": week_start,
                    "completed_at__date__lte": today,
                },
            ),
            (
                LeaderboardEntry.PeriodType.THIS_MONTH,
                month_key,
                {
                    "completed_at__date__gte": month_start,
                    "completed_at__date__lte": today,
                },
            ),
            (
                LeaderboardEntry.PeriodType.ALL_TIME,
                "all_time",
                {},
            ),
        ]

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

            zone_name = rider.home_zone.name if rider.home_zone else ""
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

        LeaderboardEntry.objects.bulk_create(entries)
        self.stdout.write(f"     {len(entries)} riders ranked.")
