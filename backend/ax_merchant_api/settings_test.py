import os
from .settings import *

# Override DATABASES explicitly to target the containerized Postgres database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "axpress_test"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "password"),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# Speed up test runner with lightweight password hasher
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Run Celery tasks synchronously in-process
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use clean, fast in-memory cache for isolation
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Deactivate Sentry/logger external integrations if present
# Ensure no live services are hit
PAYSTACK_SECRET_KEY = "sk_test_mockkey"
PAYSTACK_PUBLIC_KEY = "pk_test_mockkey"
SMARTPARCEL_API_KEY = "smartparcel_test_key"
SMARTPARCEL_SECRET_KEY = "smartparcel_test_secret"
ABLY_API_KEY = "ably_test_key"
RESPOND_IO_API_KEY = "respond_io_test_key"
GOOGLE_MAPS_API_KEY = "google_maps_test_key"
ROUTING_SERVICE_API_KEY = "routing_test_key"
