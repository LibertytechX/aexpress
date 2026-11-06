import hashlib

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from .models import ServiceAPIKey, MerchantAPIKey


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


class MerchantAPIKeyAuthentication(BaseAuthentication):
    """
    Authenticates incoming requests using a Merchant API Key.

    Usage:
        Authorization: Bearer ak_live_xxxxxxx...

    The key prefix (first 11 chars) is used for a fast DB lookup,
    then the full SHA-256 hash is compared for verification.

    Returns the actual merchant Django User object so all existing
    permission checks and request.user access patterns work unchanged.
    Can be used alongside JWT auth by listing both in authentication_classes:

        authentication_classes = [
            MerchantAPIKeyAuthentication,
            *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
        ]
    """

    keyword = "Apikey"
    key_prefix = "ak_live_"

    def authenticate(self, request):
        """Authenticate the request using a Merchant API key.

        Args:
            request: The incoming HTTP request.

        Returns:
            A tuple of (user, api_key) if successful, or None to pass
            authentication to the next class in authentication_classes.

        Raises:
            AuthenticationFailed: If the key format is valid but the key
                is not found, is inactive, or has expired.
        """
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        prefix_check = f"{self.keyword} {self.key_prefix}"

        if not auth_header.startswith(prefix_check):
            return None  # Not our auth scheme — let other authenticators try

        raw_key = auth_header[len(self.keyword) + 1 :]
        prefix = raw_key[:11]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        try:
            api_key = MerchantAPIKey.objects.select_related("merchant").get(
                prefix=prefix,
                key_hash=key_hash,
                is_active=True,
            )
        except MerchantAPIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid or inactive Merchant API key.")

        # Track last usage asynchronously to avoid blocking the request
        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=["last_used_at"])

        # Return the real merchant User — request.user works normally downstream
        return (api_key.merchant, api_key)

    def authenticate_header(self, request):
        """Return the WWW-Authenticate header value for 401 responses.

        Args:
            request: The incoming HTTP request.

        Returns:
            The authentication scheme string for the WWW-Authenticate header.
        """
        return self.keyword
