from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Order
from riders.models import OrderOffer
from dispatcher.models import SystemSettings
from datetime import timedelta
from decimal import Decimal


@receiver(post_save, sender=Order)
def create_order_offer(sender, instance, created, **kwargs):
    if created:
        # Get system settings for timeout
        settings, _ = SystemSettings.objects.get_or_create(id=1)
        timeout = settings.accept_timeout_sec or 120

        # Calculate expiration time
        expires_at = timezone.now() + timedelta(seconds=timeout)

        # Calculate estimated earnings (80% of total_amount)
        total_amount = Decimal(str(instance.total_amount or 0))
        estimated_earnings = (total_amount * Decimal("0.2")).quantize(Decimal("0.01"))

        # Create unassigned offer
        OrderOffer.objects.create(
            order=instance,
            rider=None,
            status=OrderOffer.Status.PENDING,
            estimated_earnings=estimated_earnings,
            expires_at=expires_at,
        )
