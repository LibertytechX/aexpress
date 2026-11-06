from django.db import models


# Create your models here.
class ErrorLog(models.Model):
    app_name = models.CharField(
        max_length=100,
        default="exception_handler",
    )
    traceback = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    severity = models.CharField(
        max_length=10,
        choices=[("ERROR", "Error"), ("WARNING", "Warning")],
        default="ERROR",
    )

    def __str__(self):
        return f"{self.severity} - " f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
