import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from orders.models import Order, OrderEvent

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to update all orders with status 'AssignmentAccepted' to 'Assigned'.
    """

    help = "Updates orders from 'AssignmentAccepted' to 'Assigned' and logs events."

    def handle(self, *args, **options) -> None:
        """
        Execute the management command.
        """
        self.stdout.write(
            self.style.SUCCESS("Starting order status update from AssignmentAccepted to Assigned...")
        )

        orders_to_update = Order.objects.filter(status="AssignmentAccepted")
        count = orders_to_update.count()

        if count == 0:
            self.stdout.write(self.style.WARNING("No orders found with status 'AssignmentAccepted'."))
            return

        updated_count = 0
        try:
            with transaction.atomic():
                for order in orders_to_update:
                    old_status = order.status
                    order.status = "Assigned"
                    order.save(update_fields=["status", "updated_at"])
                    updated_count += 1


            self.stdout.write(
                self.style.SUCCESS(f"Successfully updated {updated_count} orders to 'Assigned'.")
            )
            logger.info(f"Successfully updated {updated_count} orders from AssignmentAccepted to Assigned.")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
            logger.error(f"Error updating order statuses: {str(e)}")
