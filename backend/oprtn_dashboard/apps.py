from django.apps import AppConfig


class OprtnDashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "oprtn_dashboard"
    verbose_name = "Operations Dashboard"

    def ready(self):
        # Import signal handlers (currently a no-op placeholder; see signals.py).
        import oprtn_dashboard.signals  # noqa: F401
