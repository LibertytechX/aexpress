from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Wallet, AmortizationWallet
from .corebanking_service import create_virtual_account


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    Signal to automatically create a wallet when a new user is created
    """
    if created:
        Wallet.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_wallet(sender, instance, **kwargs):
    """
    Signal to save wallet when user is saved
    """
    if not hasattr(instance, "wallet"):
        Wallet.objects.create(user=instance)


@receiver(post_save, sender=AmortizationWallet)
def create_amortization_wallet_account_detail(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        create_virtual_account(user, True)
