from django.core.management.base import BaseCommand
from subscriptions.models import PostpaidPlan


class Command(BaseCommand):
    help = "Seed initial postpaid plans"

    def handle(self, *args, **options):
        plans = [
            {"name": "Weekly Postpaid", "plan_type": "weekly"},
            {"name": "Monthly Postpaid", "plan_type": "monthly"},
        ]

        for plan_data in plans:
            plan, created = PostpaidPlan.objects.update_or_create(
                name=plan_data["name"],
                defaults={"plan_type": plan_data["plan_type"], "is_active": True},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created plan: {plan.name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated plan: {plan.name}"))
