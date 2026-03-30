from django.core.management.base import BaseCommand
from django.db import transaction
from dispatcher.models import Rider, RelayNode


class Command(BaseCommand):
    help = "Updates the hub field of riders based on their home_zone name."

    def handle(self, *args, **options):
        # We only process riders that have a home_zone and whose hub hasn't already been set
        # (Though we can update all just in case their home_zone changed).
        riders = Rider.objects.filter(home_zone__isnull=False)
        updated_count = 0
        not_found_count = 0

        with transaction.atomic():
            for rider in riders:
                zone_name = rider.home_zone.name

                # Find relay node with similar name (case-insensitive exact match)
                relay_node = RelayNode.objects.filter(name__iexact=zone_name).first()

                if relay_node:
                    rider.hub = relay_node
                    rider.save(update_fields=["hub"])
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Updated rider {rider} with hub '{relay_node.name}'"
                        )
                    )
                else:
                    not_found_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Could not find RelayNode with name '{zone_name}' for rider {rider}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted: successfully updated {updated_count} riders. {not_found_count} hubs not found."
            )
        )
