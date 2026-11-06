from django.apps import AppConfig


class RidersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "riders"

    def ready(self) -> None:
        """Initialize the app configuration, including importing signal handlers."""
        try:
            import firebase
        except ImportError:
            pass

        import riders.signals  # noqa
