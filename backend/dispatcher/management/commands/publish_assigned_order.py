from django.core.management.base import BaseCommand, CommandError
from orders.models import Order
from dispatcher.models import Rider


class Command(BaseCommand):
    help = (
        "Manually publish an 'order_assigned' Ably event for a given order. "
        "Usage: python manage.py publish_assigned_order <order_number> [--rider <rider_id>]"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "order_number",
            type=str,
            help="The order number of the order to publish (e.g. ORD-00123)",
        )
        parser.add_argument(
            "--rider",
            dest="rider_id",
            type=str,
            default=None,
            help=(
                "Rider ID to publish to (e.g. RID-001). "
                "Defaults to the rider already assigned on the order."
            ),
        )

    def handle(self, *args, **options):
        from riders.views import publish_order_assigned_event

        order_number = options["order_number"]
        rider_id = options.get("rider_id")

        # Resolve the order
        try:
            order = Order.objects.select_related("rider", "rider__user").get(
                order_number=order_number
            )
        except Order.DoesNotExist:
            raise CommandError(f"Order '{order_number}' not found.")

        # Resolve the rider
        if rider_id:
            try:
                rider = Rider.objects.get(rider_id=rider_id)
            except Rider.DoesNotExist:
                raise CommandError(f"Rider '{rider_id}' not found.")
        elif order.rider:
            rider = order.rider
        else:
            raise CommandError(
                f"Order '{order_number}' has no assigned rider. "
                "Pass --rider <rider_id> to specify one."
            )

        self.stdout.write(
            f"Publishing order_assigned event for order {order.order_number} "
            f"→ channel assigned-{rider.rider_id} ..."
        )

        publish_order_assigned_event(order, rider)

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Published to Ably channel 'assigned-{rider.rider_id}'"
            )
        )
