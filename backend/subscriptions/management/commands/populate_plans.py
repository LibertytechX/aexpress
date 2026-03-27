from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan
from decimal import Decimal


class Command(BaseCommand):
    help = "Populate default subscription plans: Starter, Growth, Enterprise"

    def handle(self, *args, **options):
        plans = [
            {
                "name": "Starter",
                "price": Decimal("300000.00"),
                "free_orders_limit": 150,
                "overage_fee": Decimal("1500.00"),
                "has_dedicated_rider": False,
            },
            {
                "name": "Growth",
                "price": Decimal("550000.00"),
                "free_orders_limit": 300,
                "overage_fee": Decimal("1200.00"),
                "has_dedicated_rider": True,
            },
            {
                "name": "Enterprise",
                "price": Decimal("750000.00"),
                "free_orders_limit": 450,
                "overage_fee": Decimal("1000.00"),
                "has_dedicated_rider": True,
            },
        ]

        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data["name"], defaults=plan_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created plan: {plan.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated plan: {plan.name}"))

        self.stdout.write(
            self.style.SUCCESS("Successfully populated subscription plans.")
        )
