from decimal import Decimal
from typing import Any, Type
from django.db.models.signals import post_save
from django.dispatch import receiver
from riders.models import RiderEarning
from wallet.models import Wallet


@receiver(post_save, sender=RiderEarning)
def credit_rider_wallet_on_earning(
    sender: Type[RiderEarning],
    instance: RiderEarning,
    created: bool,
    **kwargs: Any,
) -> None:
    """Credits the rider's wallet when a new RiderEarning is created.

    Args:
        sender: The model class.
        instance: The RiderEarning instance.
        created: A boolean indicating whether a new record was created.
        **kwargs: Additional keyword arguments.
    """
    if created:
        rider = instance.rider
        amount = instance.net_earning
        order = instance.order

        # Retrieve or create the rider's wallet
        wallet, _ = Wallet.objects.get_or_create(user=rider.user)

        # Build clean description and reference
        description = f"Trip earning: {order.order_number}"
        reference = f"EARN-{order.order_number}-{instance.id}"[:100]

        # Atomically credit the wallet
        wallet.credit(
            amount=amount,
            description=description,
            reference=reference,
        )
