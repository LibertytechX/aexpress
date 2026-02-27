from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from riders.notifications import notify_rider

User = get_user_model()


class Command(BaseCommand):
    help = "Send a push notification and persist it for a given rider by phone number"

    def add_arguments(self, parser):
        parser.add_argument("phone_number", type=str, help="The rider's phone number")
        parser.add_argument("title", type=str, help="The notification title")
        parser.add_argument("body", type=str, help="The notification body content")

    def handle(self, *args, **kwargs):
        phone_number = kwargs["phone_number"]
        title = kwargs["title"]
        body = kwargs["body"]

        try:
            user = User.objects.get(phone=phone_number)
            rider = user.rider_profile

            # Use the existing notify_rider function which sends FCM AND creates RiderNotification
            notify_rider(
                rider=rider, title=title, body=body, data={"source": "cli_command"}
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully queued notification for rider {rider.rider_id} (Phone: {phone_number})"
                )
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"User with phone number {phone_number} does not exist."
                )
            )
        except getattr(User, "rider_profile").RelatedObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"User with phone number {phone_number} is not a rider."
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
