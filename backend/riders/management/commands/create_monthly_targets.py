"""
create_monthly_targets — management command
Creates RiderMonthlyTarget for all active riders for the current month
if one doesn't already exist.

Run on the 1st of each month via cron:
  python manage.py create_monthly_targets
  python manage.py create_monthly_targets --month 2026-04  (override month)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import calendar

from dispatcher.models import Rider
from riders.models import RiderMonthlyTarget, RiderEarning


# Default daily order target (used for auto-calculation)
DEFAULT_DAILY_TARGET = 25
# Default average fare per order (₦) for auto-calc
DEFAULT_AVG_FARE = Decimal("750.00")


class Command(BaseCommand):
    help = "Creates RiderMonthlyTarget entries for all active riders for the current (or given) month."

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=str,
            default=None,
            help="Month to create targets for (YYYY-MM). Defaults to current month.",
        )
        parser.add_argument(
            "--target-earnings",
            type=float,
            default=None,
            help="Override target earnings amount (₦). If not set, auto-calculated.",
        )

    def handle(self, *args, **options):
        raw_month = options.get("month")
        override_target = options.get("target_earnings")

        if raw_month:
            year, month = map(int, raw_month.split("-"))
            month_date = timezone.datetime(year, month, 1).date()
        else:
            today = timezone.now().date()
            month_date = today.replace(day=1)

        self.stdout.write(
            f"📅 Creating monthly targets for {month_date.strftime('%B %Y')}..."
        )

        # Working days in the month (Mon–Fri only)
        num_days = calendar.monthrange(month_date.year, month_date.month)[1]
        working_days = sum(
            1
            for d in range(1, num_days + 1)
            if timezone.datetime(month_date.year, month_date.month, d).weekday() < 5
        )

        if override_target:
            target_earnings = Decimal(str(override_target))
            is_auto = False
        else:
            # Auto-calc: 25 orders/day × avg fare × working days
            target_earnings = DEFAULT_DAILY_TARGET * DEFAULT_AVG_FARE * working_days
            is_auto = True

        active_riders = Rider.objects.filter(is_active=True, is_authorized=True)
        created = 0
        skipped = 0

        for rider in active_riders:
            _, was_created = RiderMonthlyTarget.objects.get_or_create(
                rider=rider,
                month=month_date,
                defaults={
                    "target_earnings": target_earnings,
                    "target_orders_per_day": DEFAULT_DAILY_TARGET,
                    "is_auto": is_auto,
                },
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Done — {created} targets created, {skipped} already existed. "
                f"Target: ₦{target_earnings:,.0f} (auto={is_auto})"
            )
        )
