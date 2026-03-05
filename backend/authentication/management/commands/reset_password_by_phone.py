from django.core.management.base import BaseCommand, CommandError
from authentication.models import User
import getpass


class Command(BaseCommand):
    help = "Sets a new password for a user given their phone number"

    def add_arguments(self, parser):
        parser.add_argument("phone", type=str, help="The phone number of the user")
        parser.add_argument(
            "--password",
            type=str,
            help="The new password (optional, will prompt if not provided)",
        )

    def handle(self, *args, **options):
        phone = options["phone"]
        password = options.get("password")

        try:
            # Clean the phone number (remove spaces, dashes if any)
            phone = phone.replace(" ", "").replace("-", "")
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise CommandError(f'User with phone number "{phone}" does not exist.')

        if not password:
            while True:
                password = getpass.getpass(
                    f"Enter new password for {user.email or user.phone}: "
                )
                password_confirm = getpass.getpass("Enter new password again: ")
                if password == password_confirm:
                    break
                self.stdout.write(
                    self.style.ERROR("Passwords do not match. Please try again.")
                )

        user.set_password(password)
        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully changed password for user {user.email or user.phone}"
            )
        )
