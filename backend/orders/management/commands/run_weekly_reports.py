from django.core.management.base import BaseCommand
from orders.tasks import process_weekly_monday_reports

class Command(BaseCommand):
    help = 'Runs the process_weekly_monday_reports task manually'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting process_weekly_monday_reports...'))
        try:
            process_weekly_monday_reports()
            self.stdout.write(self.style.SUCCESS('Successfully completed process_weekly_monday_reports.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running process_weekly_monday_reports: {e}'))
