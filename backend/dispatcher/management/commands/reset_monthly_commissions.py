from django.core.management.base import BaseCommand
from dispatcher.services import reset_monthly_commissions_service


class Command(BaseCommand):
    help = "Resets monthly commissions for all dispatchers, rolling previous month into previous_month_commission."

    def handle(self, *args, **options):
        self.stdout.write("Starting monthly commission rollover...")
        count = reset_monthly_commissions_service()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully rolled over monthly commissions for {count} dispatcher(s)."
            )
        )
