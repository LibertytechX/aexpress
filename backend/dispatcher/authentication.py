import hashlib

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from .models import ServiceAPIKey


class ServiceUser:
    """Dummy user object for service-to-service auth (OCC → Main Backend)."""

    is_authenticated = True
    is_active = True
    is_staff = False
    is_superuser = False
    pk = None
    id = None

    def __init__(self, api_key):
        self.api_key = api_key
        self.scopes = api_key.scopes
        self.service_name = api_key.name


class ServiceAPIKeyAuthentication(BaseAuthentication):
    """
    Authenticates requests from the OCC backend using:
        Authorization: Bearer sk_xxxxx...

    The key prefix (first 11 chars) is used for a fast DB lookup,
    then the full SHA-256 hash is compared for verification.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith(f"{self.keyword} sk_"):
            return None  # Not our auth scheme — let other authenticators try

        raw_key = auth_header[len(self.keyword) + 1 :]
        prefix = raw_key[:11]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        try:
            api_key = ServiceAPIKey.objects.get(
                prefix=prefix,
                key_hash=key_hash,
                is_active=True,
            )
        except ServiceAPIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid service API key.")

        if api_key.expires_at and api_key.expires_at < timezone.now():
            raise AuthenticationFailed("Service API key has expired.")

        # Track last usage
        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=["last_used_at"])

        return (ServiceUser(api_key), api_key)
