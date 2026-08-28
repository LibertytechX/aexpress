"""Global pytest fixtures configuration for Django backend service."""

from typing import Any, Generator, Tuple
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

# Register all autouse mockers by importing their fixture functions directly.
from test_utils.mockers.celery import celery_eager  # noqa: F401
from test_utils.mockers.http_external import mock_external_http  # noqa: F401
from test_utils.mockers.signals import disable_signals  # noqa: F401

from test_utils.factories.accounts import UserFactory
from authentication.models import User


# ── Storage & Cache fixtures ───────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def override_static_storage(settings: Any) -> None:
    """Fixture to override staticfiles storage during pytest execution to prevent missing manifest errors.

    Args:
        settings: Pytest Django settings object.
    """
    settings.STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }


@pytest.fixture(autouse=True)
def reset_cache() -> Generator[None, None, None]:
    """Clear Django cache before and after every test."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


# ── Common user fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def base_user(db: Any) -> User:
    """Fixture to provide a plain active User model instance.

    Args:
        db: Pytest database marker.

    Returns:
        User: Factory-generated active user.
    """
    return UserFactory()


# ── API client fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def api_client() -> APIClient:
    """Fixture to provide an unauthenticated DRF APIClient instance.

    Returns:
        APIClient: Unauthenticated REST framework test client.
    """
    return APIClient()


@pytest.fixture
def authenticated_client(db: Any) -> Generator[APIClient, None, None]:
    """Fixture to provide a factory-created user and an authenticated APIClient.

    Args:
        db: Pytest database marker.

    Returns:
        Generator[APIClient, None, None]: Configured APIClient authenticated with user.
    """
    client: APIClient = APIClient()
    user: User = UserFactory()
    client.force_authenticate(user=user)
    yield client


@pytest.fixture
def auth_client(base_user: User) -> Tuple[APIClient, User]:
    """DRF APIClient authenticated as a plain user with JWT Bearer token header.

    Args:
        base_user: The user to authenticate.

    Returns:
        Tuple[APIClient, User]: Authenticated APIClient and the associated User instance.
    """
    client: APIClient = APIClient()
    token = RefreshToken.for_user(base_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client, base_user
