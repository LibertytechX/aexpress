import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

# Register all autouse mockers by importing their fixture functions directly.
from test_utils.mockers.celery import celery_eager  # noqa: F401
from test_utils.mockers.http_external import mock_external_http  # noqa: F401
from test_utils.mockers.signals import disable_signals  # noqa: F401

from test_utils.factories.accounts import UserFactory


# ── Cache reset ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_cache():
    """Clear Django cache before and after every test."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


# ── Common user fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def base_user(db):
    """A plain active User."""
    return UserFactory()


# ── API client fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    """Unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def auth_client(base_user):
    """DRF APIClient authenticated as a plain user. Returns (client, user)."""
    client = APIClient()
    token = RefreshToken.for_user(base_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client, base_user
