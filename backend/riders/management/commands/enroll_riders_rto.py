"""
enroll_riders_rto — management command
Enrolls riders into the Ride to Own program.
By default, it finds all active riders with a vehicle_asset assigned who are not yet enrolled.

Usage:
  python manage.py enroll_riders_rto
  python manage.py enroll_riders_rto --rider AX001  (specific rider)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from dispatcher.models import Rider
from riders.models import RideToOwnConfig, RideToOwnEnrollment


class Command(BaseCommand):
    help = (
        "Enrolls riders into the Ride to Own program based on assigned vehicle assets."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--rider",
            type=str,
            help="Specific Rider ID (short code) to enroll.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Enroll even if the rider doesn't have a vehicle_asset assigned.",
        )

    def handle(self, *args, **options):
        rider_id = options.get("rider")
        force = options.get("force")

        # 1. Ensure config exists
        config = RideToOwnConfig.get_active()
        if not config:
            self.stdout.write(
                "⚠️ No active RideToOwnConfig found. Creating default (7800 orders / 12 months)..."
            )
            config = RideToOwnConfig.objects.create(
                total_orders_target=7800,
                program_duration_months=12,
                description="Default Ride to Own program.",
            )

        # 2. Get target riders
        if rider_id:
            try:
                riders = [Rider.objects.get(rider_id=rider_id)]
            except Rider.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Rider {rider_id} not found."))
                return
        else:
            # All active riders with assets not already enrolled
            riders = Rider.objects.filter(
                is_active=True, vehicle_asset__isnull=False
            ).exclude(ride_to_own__isnull=False)

        if not riders:
            self.stdout.write("ℹ️ No eligible riders found for enrollment.")
            return

        self.stdout.write(f"🚜 Enrolling {len(riders)} riders...")

        created_count = 0
        skipped_count = 0

        today = timezone.now().date()
        end_date = today + relativedelta(months=config.program_duration_months)

        for rider in riders:
            # Check if already enrolled (if specific rider was passed)
            if hasattr(rider, "ride_to_own"):
                self.stdout.write(f"  ⏭️ {rider.rider_id} is already enrolled.")
                skipped_count += 1
                continue

            if not rider.vehicle_asset and not force:
                self.stdout.write(
                    f"  ⚠️ Skipping {rider.rider_id}: No vehicle_asset assigned (use --force to override)."
                )
                skipped_count += 1
                continue

            RideToOwnEnrollment.objects.create(
                rider=rider,
                vehicle_asset=rider.vehicle_asset,
                start_date=today,
                end_date=end_date,
                is_active=True,
            )
            created_count += 1
            self.stdout.write(f"  ✅ Enrolled {rider.rider_id} (ends {end_date})")

        self.stdout.write(
            self.style.SUCCESS(
                f"🎉 Done — {created_count} riders enrolled, {skipped_count} skipped."
            )
        )
