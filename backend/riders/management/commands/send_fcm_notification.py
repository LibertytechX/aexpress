from django.core.management.base import BaseCommand
from authentication.models import User
from riders.notifications import notify_rider


class Command(BaseCommand):
    help = "Send an FCM push notification to a rider identified by their phone number"

    def add_arguments(self, parser):
        parser.add_argument(
            "phone", type=str, help="Rider's phone number (e.g. +2348012345678)"
        )
        parser.add_argument(
            "--title", type=str, default="Hello!", help="Notification title"
        )
        parser.add_argument(
            "--body",
            type=str,
            default="You have a new message.",
            help="Notification body",
        )
        parser.add_argument(
            "--data",
            nargs="*",
            metavar="KEY=VALUE",
            help="Optional key=value pairs to include as data payload (e.g. --data type=order order_id=42)",
            default=[],
        )

    def handle(self, *args, **options):
        phone = options["phone"]
        title = options["title"]
        body = options["body"]

        # Parse optional data payload
        data = {}
        for item in options["data"]:
            if "=" in item:
                key, _, value = item.partition("=")
                data[key.strip()] = value.strip()
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Ignoring invalid data argument: '{item}' (expected KEY=VALUE)"
                    )
                )

        # Look up user by phone
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"No user found with phone number: {phone}")
            )
            return

        # Ensure user has a rider profile
        rider = getattr(user, "rider_profile", None)
        if not rider:
            self.stdout.write(
                self.style.ERROR(f"User {phone} does not have a rider profile.")
            )
            return

        self.stdout.write(
            f"Sending notification to rider {rider.rider_id} ({user.get_full_name() or phone})..."
        )
        self.stdout.write(f"  Title : {title}")
        self.stdout.write(f"  Body  : {body}")
        if data:
            self.stdout.write(f"  Data  : {data}")

        notify_rider(rider, title, body, data=data or None)

        self.stdout.write(self.style.SUCCESS("Notification dispatched successfully."))
