from django.core.management.base import BaseCommand
from riders.models import OrderOffer


class Command(BaseCommand):
    help = "Cleans up pending order offers by changing their status to accepted if the related order is no longer pending."

    def handle(self, *args, **options):
        # Find OrderOffer instances where status is pending but the related order is not pending
        pending_offers = OrderOffer.objects.filter(
            status=OrderOffer.Status.PENDING
        ).exclude(order__status="Pending")

        count = pending_offers.count()
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS("No pending order offers require cleanup.")
            )
            return

        updated_count = pending_offers.update(status=OrderOffer.Status.ACCEPTED)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {updated_count} order offers to accepted status."
            )
        )
