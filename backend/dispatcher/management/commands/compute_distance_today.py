from __future__ import annotations

import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from dispatcher.models import VehicleAsset, VehicleTracking


class Command(BaseCommand):
    help = (
        "Compute VehicleAsset.distance_today from VehicleTracking odometer snapshots. "
        "For each asset, distance_today = max(0, last_travelled_today - first_travelled_today)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            dest="date",
            default=None,
            help="Local date to compute (YYYY-MM-DD). Defaults to today.",
        )
        parser.add_argument(
            "--reset-missing",
            action="store_true",
            help="Also set distance_today=0 for assets with no tracking rows for the date.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Compute and report counts without writing to the database.",
        )

    def handle(self, *args, **options):
        day_opt = options.get("date")
        dry_run = bool(options.get("dry_run"))
        reset_missing = bool(options.get("reset_missing"))

        day = timezone.localdate() if not day_opt else datetime.date.fromisoformat(day_opt)
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min), tz)
        end = timezone.make_aware(datetime.datetime.combine(day + datetime.timedelta(days=1), datetime.time.min), tz)

        qs = VehicleTracking.objects.filter(
            created_at__gte=start,
            created_at__lt=end,
            travelled__isnull=False,
        )

        # Postgres-only optimisation: DISTINCT ON (vehicle_asset_id)
        first_rows = qs.order_by("vehicle_asset_id", "created_at").distinct(
            "vehicle_asset_id"
        )
        last_rows = qs.order_by("vehicle_asset_id", "-created_at").distinct(
            "vehicle_asset_id"
        )

        first_map = dict(first_rows.values_list("vehicle_asset_id", "travelled"))
        last_map = dict(last_rows.values_list("vehicle_asset_id", "travelled"))

        touched_ids = set(first_map.keys()) | set(last_map.keys())
        updates: list[VehicleAsset] = []

        for asset_id in touched_ids:
            first_val = first_map.get(asset_id)
            last_val = last_map.get(asset_id)
            if first_val is None and last_val is None:
                continue
            if first_val is None:
                first_val = last_val
            if last_val is None:
                last_val = first_val

            delta = last_val - first_val
            if delta < 0:
                delta = Decimal("0.00")
            else:
                delta = Decimal(str(delta)).quantize(Decimal("0.01"))

            updates.append(VehicleAsset(id=asset_id, distance_today=delta))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] {day.isoformat()}: would update {len(updates)} assets"
                )
            )
            if reset_missing:
                missing_qs = VehicleAsset.objects.exclude(id__in=touched_ids)
                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY RUN] would reset {missing_qs.count()} assets with no telemetry for date"
                    )
                )
            return

        if updates:
            VehicleAsset.objects.bulk_update(updates, ["distance_today"], batch_size=1000)

        reset_count = 0
        if reset_missing:
            reset_count = (
                VehicleAsset.objects.exclude(id__in=touched_ids)
                .exclude(distance_today__isnull=True)
                .update(distance_today=Decimal("0.00"))
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"{day.isoformat()}: updated={len(updates)} reset_missing={reset_count}"
            )
        )

