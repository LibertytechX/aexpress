from django.db.models.signals import post_save
from django.dispatch import receiver
import threading
from django.contrib.auth import get_user_model
from .models import Rider, DispatcherProfile, Merchant

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.usertype == "Dispatcher":
            DispatcherProfile.objects.create(user=instance)
        elif instance.usertype == "Rider":
            Rider.objects.create(user=instance)
        elif instance.usertype == "Merchant":
            referral_code = getattr(instance, "referral_code", None)
            acquisition_source = instance.registration_source

            if referral_code:
                from referrals.models import LibertyPayUser

                if LibertyPayUser.objects.filter(referral_code=referral_code).exists():
                    acquisition_source = "referral"
                else:
                    referral_code = None

            Merchant.objects.create(
                user=instance,
                acquisition_source=acquisition_source,
                referral_code=referral_code,
            )

            # Trigger merchant-created webhook in background
            def _trigger_merchant_created():
                try:
                    from webhooks.utils import trigger_webhook
                    from authentication.serializers import UserSerializer

                    payload = {
                        "event": "merchant-created",
                        "timestamp": instance.created_at.isoformat(),
                        "data": UserSerializer(instance).data,
                    }
                    trigger_webhook("merchant-created", payload)
                except Exception as e:
                    import logging

                    logging.getLogger(__name__).error(
                        f"Failed to trigger merchant-created webhook from signal: {e}"
                    )

            threading.Thread(target=_trigger_merchant_created, daemon=True).start()
