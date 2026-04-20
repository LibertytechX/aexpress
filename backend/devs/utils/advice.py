from functools import wraps
import traceback
from devs.models import ErrorLog
from django.utils import timezone


def log_exception_advice(app_name: str) -> any:

    def decorator(func):
        # decorator wrapper
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Decorator wrapper function"""
            try:
                return func(*args, **kwargs)
            except Exception:
                stack_trace = traceback.format_exc()
                traceback.print_exc()
                ErrorLog.objects.create(
                    traceback=stack_trace,
                    severity="ERROR",
                    timestamp=timezone.now(),
                    app_name=app_name,
                )
                # Re-raise so callers can handle the failure instead of silently returning None.
                raise

        return wrapper

    return decorator
