from django.contrib import admin
from .models import ErrorLog


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ["severity", "timestamp", "app_name", "traceback"]
    search_fields = [
        "severity",
        "app_name",
    ]
    list_filter = ["severity", "timestamp"]
    ordering = ["-timestamp"]
