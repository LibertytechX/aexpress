"""Create repeatable merchant data for exercising password-reset endpoints."""

from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from dispatcher.models import Merchant

from authentication.models import Address


User = get_user_model()


class Command(BaseCommand):
    help = "Seed merchant users, profiles, addresses, and valid password-reset tokens."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of test merchant records to create (default: 100).",
        )
        parser.add_argument(
            "--password",
            default="password123",
            help="Password assigned to each seeded user.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        if count < 1:
            raise ValueError("--count must be at least 1")

        created_users = 0
        updated_users = 0
        created_addresses = 0
        now = timezone.now()

        with transaction.atomic():
            for index in range(1, count + 1):
                email = f"user-password-reset-{index}@axpress.test"
                phone = f"+234910{index:07d}"

                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "phone": phone,
                        "usertype": "Merchant",
                        "first_name": "Reset",
                        "last_name": f"Tester {index}",
                        "business_name": f"Password Reset Merchant {index}",
                        "contact_name": f"Reset Tester {index}",
                        "address": f"{index} Test Street, Lagos",
                        "registration_source": "password-reset-seed",
                        "email_verified": True,
                        "phone_verified": True,
                    },
                )

                user.set_password(options["password"])
                user.usertype = "Merchant"
                user.password_reset_token = uuid4().hex
                user.password_reset_token_created = now
                user.email_verified = True
                user.phone_verified = True
                user.save(
                    update_fields=[
                        "password",
                        "usertype",
                        "password_reset_token",
                        "password_reset_token_created",
                        "email_verified",
                        "phone_verified",
                    ]
                )

                if created:
                    created_users += 1
                else:
                    updated_users += 1

                Merchant.objects.get_or_create(
                    user=user,
                    defaults={"acquisition_source": "password-reset-seed"},
                )

                _, address_created = Address.objects.update_or_create(
                    user=user,
                    label="Test Office",
                    defaults={
                        "address": f"{index} Test Street, Lagos",
                        "is_default": True,
                    },
                )
                if address_created:
                    created_addresses += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {count} password-reset users "
                f"({created_users} created, {updated_users} refreshed) and "
                f"{created_addresses} addresses."
            )
        )
        self.stdout.write(
            "Emails use the pattern user-password-reset-<n>@axpress.test; "
            "tokens are stored on each User.password_reset_token."
        )
