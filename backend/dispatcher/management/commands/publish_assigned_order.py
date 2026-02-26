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
        import asyncio
        from django.conf import settings
        from ably import AblyRest
        from orders.serializers import AssignedOrderSerializer

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
            _ = order.rider
        else:
            raise CommandError(
                f"Order '{order_number}' has no assigned rider. "
                "Pass --rider <rider_id> to specify one."
            )

        api_key = getattr(settings, "ABLY_API_KEY", "")
        if not api_key:
            raise CommandError("ABLY_API_KEY is not configured in settings.")

        channel_name = f"assigned-37c34182-7244-494f-a902-a1cd0a8e69cd"
        payload = AssignedOrderSerializer(order).data

        self.stdout.write(
            f"Publishing order_assigned event for order {order.order_number} "
            f"→ channel {channel_name} ..."
        )

        async def _publish():
            client = AblyRest(api_key)
            channel = client.channels.get(
                "for-you"
            )
            await channel.publish("order_assigned", payload)

        asyncio.run(_publish())

        self.stdout.write(
            self.style.SUCCESS(f"✓ Published to Ably channel '{channel_name}'")
        )
