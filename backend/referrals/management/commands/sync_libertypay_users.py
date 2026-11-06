from django.core.management.base import BaseCommand
from referrals.tasks import sync_libertypay_users_task


class Command(BaseCommand):
    help = "Syncs LibertyPay users from the external API into the database."

    def handle(self, *args, **options):
        self.stdout.write("Starting LibertyPay user sync...")
        # Call the task synchronously for the management command
        result = sync_libertypay_users_task()
        if "Success" in result:
            self.stdout.write(self.style.SUCCESS(result))
        else:
            self.stdout.write(self.style.ERROR(result))
