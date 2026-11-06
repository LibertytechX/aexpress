from django.core.management.base import BaseCommand
from django.db.models import Count
from dispatcher.models import Vertical, Zone, RelayNode, Rider, Merchant, ZoneCaptain, VerticalLead


class Command(BaseCommand):
    help = "Diagnose the vertical → zone → rider hierarchy to find broken FK links."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== VERTICALS ==="))
        verticals = Vertical.objects.prefetch_related("zones").all()
        for v in verticals:
            active_zones = v.zones.filter(is_active=True)
            all_zones = v.zones.all()
            self.stdout.write(
                f"  [{v.code}] {v.name} (id={v.id}, active={v.is_active})"
                f"\n      active zones: {active_zones.count()}, "
                f"total zones: {all_zones.count()}"
            )
            for z in all_zones:
                rider_count = Rider.objects.filter(hub__zone=z).count()
                self.stdout.write(
                    f"        -> {z.name} (id={z.id}, active={z.is_active}, "
                    f"riders={rider_count})"
                )

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== ORPHAN ZONES (vertical=NULL) ==="))
        orphan_zones = Zone.objects.filter(vertical__isnull=True)
        if not orphan_zones.exists():
            self.stdout.write("  None — all zones are linked to a vertical.")
        for z in orphan_zones:
            rider_count = Rider.objects.filter(hub__zone=z).count()
            merchant_count = Merchant.objects.filter(zone=z).count()
            relay_count = RelayNode.objects.filter(zone=z).count()
            self.stdout.write(
                f"  {z.name} (id={z.id}, active={z.is_active})"
                f"\n      riders={rider_count}, merchants={merchant_count}, "
                f"relay_nodes={relay_count}"
            )

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== ORPHAN RIDERS (hub=NULL) ==="))
        orphan_riders = Rider.objects.filter(hub__isnull=True)
        self.stdout.write(f"  Count: {orphan_riders.count()}")

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== ORPHAN MERCHANTS (zone=NULL) ==="))
        orphan_merchants = Merchant.objects.filter(zone__isnull=True)
        self.stdout.write(f"  Count: {orphan_merchants.count()}")

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== INACTIVE ZONES WITH RIDERS ==="))
        inactive_with_riders = Zone.objects.filter(is_active=False).annotate(
            rc=Count("riders")
        ).filter(rc__gt=0)
        if not inactive_with_riders.exists():
            self.stdout.write("  None.")
        for z in inactive_with_riders:
            self.stdout.write(
                f"  {z.name} (id={z.id}) — {z.rc} riders still assigned"
            )

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== SUMMARY ==="))
        self.stdout.write(f"  Total verticals:  {Vertical.objects.count()}")
        self.stdout.write(f"  Total zones:      {Zone.objects.count()} "
                          f"(active: {Zone.objects.filter(is_active=True).count()})")
        self.stdout.write(f"  Total riders:     {Rider.objects.count()}")
        self.stdout.write(f"  Total merchants:  {Merchant.objects.count()}")
        self.stdout.write(f"  Total relay nodes:{RelayNode.objects.count()}")
        self.stdout.write(
            f"  Zones with vertical: "
            f"{Zone.objects.filter(vertical__isnull=False).count()}"
        )
        self.stdout.write(
            f"  Zones without vertical: "
            f"{Zone.objects.filter(vertical__isnull=True).count()}"
        )
        self.stdout.write("")
