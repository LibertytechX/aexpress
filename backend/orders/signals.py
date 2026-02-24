from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from riders.models import OrderOffer
from decimal import Decimal


@receiver(post_save, sender=Order)
def create_order_offer(sender, instance, created, **kwargs):
    if created:
        # Calculate estimated earnings (80% of total_amount)
        total_amount = Decimal(str(instance.total_amount or 0))
        estimated_earnings = (total_amount * Decimal("0.2")).quantize(Decimal("0.01"))

        OrderOffer.objects.create(
            order=instance,
            rider=None,
            status=OrderOffer.Status.PENDING,
            estimated_earnings=estimated_earnings,
        )
