from django.apps import AppConfig


class WhatsappMessagingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "whatsapp_messaging"
    verbose_name = "WhatsApp Messaging"

    # def ready(self):
    #     import whatsapp_messaging.signals  # noqa: F401
