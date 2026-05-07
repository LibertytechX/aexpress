from django.core.management.base import BaseCommand
from wallet.models import AmortizationWallet
from decimal import Decimal
import uuid

class Command(BaseCommand):
    help = 'Creates a mock transaction record for an amortization wallet'

    def add_arguments(self, parser):
        parser.add_argument('wallet_id', type=int, help='ID of the Amortization Wallet')
        parser.add_argument('--amount', type=float, default=1700.00, help='Amount to credit (default: 1700.00)')
        parser.add_argument('--ref', type=str, help='Custom reference (optional)')

    def handle(self, *args, **options):
        wallet_id = options['wallet_id']
        amount = Decimal(str(options['amount']))
        ref = options['ref'] or f"MOCK-{uuid.uuid4().hex[:10].upper()}"

        try:
            wallet = AmortizationWallet.objects.get(id=wallet_id)
            
            self.stdout.write(self.style.NOTICE(f"Current Balance: {wallet.balance}"))
            
            transaction = wallet.credit(
                amount=amount,
                ref=ref,
                meta={"type": "mock", "source": "management_command"}
            )
            
            wallet.refresh_from_db()
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully created transaction {transaction.reference} for {wallet.user.full_name}"
            ))
            self.stdout.write(self.style.SUCCESS(f"New Balance: {wallet.balance}"))
            self.stdout.write(self.style.SUCCESS(f"Total Paid to Date: {wallet.total_paid_to_date}"))

        except AmortizationWallet.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Amortization Wallet with ID {wallet_id} not found."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
