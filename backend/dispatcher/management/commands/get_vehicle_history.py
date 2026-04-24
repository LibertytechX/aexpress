from __future__ import annotations

import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from dispatcher.models import VehicleAsset, VehicleTracking, Rider
from django.db.models import Q

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Get vehicle tracking history for a particular rider (by riderID) within a date range."

    def add_arguments(self, parser):
        parser.add_argument(
            "rider_id", type=str, help="The rider ID (e.g. AX-1234) to search for."
        )
        parser.add_argument(
            "--start",
            type=str,
            help="Start date and optional time (format: YYYY-MM-DD or 'YYYY-MM-DD HH:MM:SS'). Defaults to start of today.",
        )
        parser.add_argument(
            "--end",
            type=str,
            help="End date and optional time (format: YYYY-MM-DD or 'YYYY-MM-DD HH:MM:SS'). Defaults to now.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Limit the number of results returned. Defaults to 100.",
        )

    def handle(self, *args, **options):
        rider_id = options["rider_id"]
        start_str = options["start"]
        end_str = options["end"]
        limit = options["limit"]

        # 1. Resolve date range
        now = timezone.now()

        if start_str:
            try:
                if " " in start_str:
                    start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                else:
                    start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                start_dt = timezone.make_aware(start_dt)
            except ValueError:
                self.stderr.write(
                    self.style.ERROR(
                        f"Invalid start date format: {start_str}. Use YYYY-MM-DD or 'YYYY-MM-DD HH:MM:SS'"
                    )
                )
                return
        else:
            # Default to start of today
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if end_str:
            try:
                if " " in end_str:
                    end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
                else:
                    end_dt = datetime.strptime(end_str, "%Y-%m-%d")
                    # If only date provided, default to end of day
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                end_dt = timezone.make_aware(end_dt)
            except ValueError:
                self.stderr.write(
                    self.style.ERROR(
                        f"Invalid end date format: {end_str}. Use YYYY-MM-DD or 'YYYY-MM-DD HH:MM:SS'"
                    )
                )
                return
        else:
            end_dt = now

        self.stdout.write(f"Searching for tracking history for rider: {rider_id}")
        self.stdout.write(f"Period: {start_dt} to {end_dt}")

        # 2. Find Rider
        rider = Rider.objects.filter(rider_id__iexact=rider_id).first()
        if not rider:
            self.stderr.write(
                self.style.ERROR(f"No Rider found with ID: {rider_id}")
            )
            return

        self.stdout.write(self.style.SUCCESS(f"Found Rider: {rider.user.contact_name or rider.user.phone}"))

        # 3. Find VehicleAsset
        asset = rider.vehicle_asset
        if not asset:
            # Fallback to plate number string on rider model
            plate = rider.vehicle_plate_number
            if plate and plate != "TEMP_PLATE":
                self.stdout.write(f"Rider has no asset linked, trying fallback plate: {plate}")
                asset = VehicleAsset.objects.filter(plate_number__iexact=plate).first()
        
        if not asset:
            self.stderr.write(
                self.style.ERROR(f"No active VehicleAsset found for rider: {rider_id}")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Found Asset: {asset.asset_id} (Plate: {asset.plate_number})"
            )
        )

        # 4. Query history
        history = VehicleTracking.objects.filter(
            vehicle_asset=asset, created_at__gte=start_dt, created_at__lte=end_dt
        ).order_by("-created_at")[:limit]

        count = history.count()
        if count == 0:
            self.stdout.write(
                self.style.WARNING("No tracking data found for this period.")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"Retrieved {count} records (limited to {limit}):")
        )

        # 5. Format output
        header = f"{'Timestamp':<25} | {'Latitude':<12} | {'Longitude':<12} | {'Travelled':<12}"
        self.stdout.write(header)
        self.stdout.write("-" * len(header))

        for record in history:
            ts = record.created_at.strftime("%Y-%m-%d %H:%M:%S")
            lat = str(record.latitude)
            lng = str(record.longitude)
            travelled = f"{record.travelled} {record.unit_of_distance or ''}"
            self.stdout.write(f"{ts:<25} | {lat:<12} | {lng:<12} | {travelled:<12}")
