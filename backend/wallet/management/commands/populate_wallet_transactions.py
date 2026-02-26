import random
import uuid
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from authentication.models import User
from wallet.models import Wallet, Transaction


TRANSACTION_TEMPLATES = [
    ("credit", "Wallet top-up via bank transfer"),
    ("credit", "Order payment received"),
    ("credit", "Refund for cancelled order"),
    ("credit", "Bonus credit"),
    ("debit", "Order payment"),
    ("debit", "Withdrawal to bank account"),
    ("debit", "Service charge"),
    ("debit", "Logistics fee deduction"),
]


class Command(BaseCommand):
    help = "Populate mock wallet transactions for a user identified by phone number"

    def add_arguments(self, parser):
        parser.add_argument("phone", type=str, help="User's phone number")
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of transactions to create (default: 10)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Spread transactions over this many past days (default: 30)",
        )
        parser.add_argument(
            "--seed-balance",
            type=float,
            default=None,
            help="Set wallet balance to this amount before creating transactions (optional)",
        )

    def handle(self, *args, **options):
        phone = options["phone"]
        count = options["count"]
        days = options["days"]
        seed_balance = options["seed_balance"]

        # ── Look up user ──────────────────────────────────────────────
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No user found with phone: {phone}"))
            return

        # ── Get or create wallet ──────────────────────────────────────
        wallet, created = Wallet.objects.get_or_create(user=user)
        if created:
            self.stdout.write(
                self.style.WARNING(
                    f"Created new wallet for {user} (no existing wallet)."
                )
            )

        if seed_balance is not None:
            wallet.balance = Decimal(str(seed_balance))
            wallet.save(update_fields=["balance"])
            self.stdout.write(f"Wallet balance seeded to ₦{wallet.balance:,}")

        # ── Generate transactions ─────────────────────────────────────
        now = timezone.now()
        self.stdout.write(
            f"Creating {count} transactions for {user} over the last {days} days..."
        )

        running_balance = wallet.balance

        for i in range(count):
            txn_type, description = random.choice(TRANSACTION_TEMPLATES)
            amount = Decimal(str(random.randint(500, 25_000)))

            # Keep balance non-negative for debits
            if txn_type == "debit":
                if running_balance < amount:
                    # Fall back to a credit so balance stays healthy
                    txn_type = "credit"
                    description = "Wallet top-up via bank transfer"
                else:
                    running_balance -= amount
            else:
                running_balance += amount

            balance_before = (
                running_balance - amount
                if txn_type == "credit"
                else running_balance + amount
            )

            # Random timestamp within the requested window
            seconds_in_window = days * 24 * 3600
            random_offset = random.randint(0, seconds_in_window)
            created_at = now - timedelta(seconds=random_offset)

            reference = f"TXN-{uuid.uuid4().hex[:12].upper()}"

            txn = Transaction(
                wallet=wallet,
                type=txn_type,
                amount=amount,
                description=description,
                reference=reference,
                balance_before=balance_before,
                balance_after=running_balance,
                status="completed",
                metadata={"source": "populate_wallet_transactions", "index": i},
            )
            # Override auto_now_add by using update_fields after save
            txn.save()

            # Patch created_at since auto_now_add prevents direct assignment at create time
            Transaction.objects.filter(pk=txn.pk).update(created_at=created_at)

            self.stdout.write(
                f"  [{i + 1:>3}] {txn_type.upper():6}  ₦{amount:>10,.2f}  "
                f"balance_after=₦{running_balance:>10,.2f}  {description}"
            )

        # Sync wallet balance to final running balance
        wallet.balance = running_balance
        wallet.save(update_fields=["balance"])

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {count} transactions created. "
                f"Wallet balance is now ₦{wallet.balance:,.2f}."
            )
        )
