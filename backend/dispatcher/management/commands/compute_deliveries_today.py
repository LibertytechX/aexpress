from __future__ import annotations

import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Q, Sum
from django.utils import timezone

from dispatcher.models import VehicleAsset
from orders.models import Order


class Command(BaseCommand):
    help = (
        "Compute VehicleAsset.deliveries_km_today by summing distance_km of all "
        "completed orders assigned to riders on each asset for the current calendar day. "
        "Run this periodically (e.g. every 5 minutes via cron) so Ably real-time "
        "payloads always carry the correct value."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            dest="date",
            default=None,
            help="Local date to compute (YYYY-MM-DD). Defaults to today.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Compute and report without writing to the database.",
        )

    def handle(self, *args, **options):
        day_opt = options.get("date")
        dry_run = bool(options.get("dry_run"))

        day = timezone.localdate() if not day_opt else datetime.date.fromisoformat(day_opt)
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min), tz)
        end = start + datetime.timedelta(days=1)

        completed_statuses = ["Done", "Delivered"]

        # Filter for orders completed today.
        # Primary signal: completed_at. Legacy fallback: updated_at when completed_at is missing.
        today_filter = Q(status__in=completed_statuses) & (
            Q(completed_at__gte=start, completed_at__lt=end)
            | Q(completed_at__isnull=True, updated_at__gte=start, updated_at__lt=end)
        )

        # Aggregate distance_km per vehicle_asset, joining through the rider.
        # We query Order directly (not through VehicleAsset) so we can group cleanly.
        rows = (
            Order.objects.filter(today_filter)
            .filter(rider__vehicle_asset__isnull=False)
            .values("rider__vehicle_asset")
            .annotate(total_km=Sum("distance_km"))
        )

        asset_km: dict[str, Decimal] = {}
        for row in rows:
            asset_id = row["rider__vehicle_asset"]
            km = row["total_km"] or Decimal("0.00")
            asset_km[str(asset_id)] = Decimal(str(km)).quantize(Decimal("0.01"))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] {day.isoformat()}: would update {len(asset_km)} asset(s) "
                    f"and reset all others to 0"
                )
            )
            for aid, km in asset_km.items():
                self.stdout.write(f"  {aid}: {km} km")
            return

        # Build bulk-update list for assets that have deliveries today
        updates: list[VehicleAsset] = []
        for asset_id, km in asset_km.items():
            updates.append(VehicleAsset(id=asset_id, deliveries_km_today=km))

        if updates:
            VehicleAsset.objects.bulk_update(updates, ["deliveries_km_today"], batch_size=500)

        # Reset all other assets to 0 so the field never shows yesterday's value
        reset_count = (
            VehicleAsset.objects.exclude(id__in=list(asset_km.keys()))
            .filter(~Q(deliveries_km_today=Decimal("0.00")) | Q(deliveries_km_today__isnull=True))
            .update(deliveries_km_today=Decimal("0.00"))
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{day.isoformat()}: updated={len(updates)} asset(s), reset={reset_count} asset(s)"
            )
        )

