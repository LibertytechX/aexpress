from django.core.management.base import BaseCommand
from wallet.models import AmortizationWallet
from dispatcher.models import Rider
from django.db import transaction


class Command(BaseCommand):
    help = "Initializes amortization wallets for all riders who do not have one"

    def handle(self, *args, **options):
        riders = Rider.objects.all()
        total_riders = riders.count()
        created_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(
            self.style.NOTICE(
                f"Found {total_riders} total riders. Starting initialization..."
            )
        )

        for rider in riders:
            user = rider.user

            # Check if user already has an amortization wallet
            if hasattr(user, "amortization_wallet"):
                skipped_count += 1
                continue

            try:
                with transaction.atomic():
                    AmortizationWallet.create_one(user)
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created amortization wallet for {user.full_name}"
                        )
                    )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to create wallet for {user.full_name}: {str(e)}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("-" * 40))
        self.stdout.write(self.style.SUCCESS(f"Initialization Complete!"))
        self.stdout.write(self.style.SUCCESS(f"Created: {created_count}"))
        self.stdout.write(
            self.style.NOTICE(f"Skipped (Already exists): {skipped_count}")
        )
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))
