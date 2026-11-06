from decimal import Decimal
import factory
from test_utils.factories.base import LibertyBaseFactory
from test_utils.factories.accounts import UserFactory
from wallet.models import Wallet, Transaction


class WalletFactory(LibertyBaseFactory):
    """
    Factory for wallet.Wallet.
    """

    class Meta:
        model = Wallet
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)
    balance = Decimal("10000.00")


class TransactionFactory(LibertyBaseFactory):
    """
    Factory for wallet.Transaction.
    """

    class Meta:
        model = Transaction

    wallet = factory.SubFactory(WalletFactory)
    type = "credit"
    amount = Decimal("1000.00")
    description = "Test Transaction"
    reference = factory.Sequence(lambda n: f"TXN-MOCK-{n:08d}")
    balance_before = Decimal("9000.00")
    balance_after = Decimal("10000.00")
    status = "completed"
