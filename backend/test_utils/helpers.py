import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
class TestCaseHelper:
    """
    Base class for all AExpress test classes.

    Inherit from this in every test class instead of unittest.TestCase.

    Provides:
    - APIClient with JWT authentication helpers
    - HTTP shorthand methods (get, post, patch, put, delete)
    - DRF response status assertions
    - DB state assertion helpers
    """

    def setup_method(self):
        self.client = APIClient()
        self.user = None

    # ── Authentication ─────────────────────────────────────────────────────────

    def authenticate(self, user):
        """Attach a JWT Bearer token for the given user to self.client."""
        self.user = user
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def authenticate_as_merchant(self, **kwargs):
        """Create and authenticate a Merchant user. Returns the user instance."""
        from test_utils.factories.accounts import UserFactory
        kwargs.setdefault("usertype", "Merchant")
        user = UserFactory(**kwargs)
        self.authenticate(user)
        return user

    def authenticate_as_rider(self, **kwargs):
        """Create and authenticate a Rider user. Returns the user instance."""
        from test_utils.factories.accounts import UserFactory
        kwargs.setdefault("usertype", "Rider")
        user = UserFactory(**kwargs)
        self.authenticate(user)
        return user

    def authenticate_as_dispatcher(self, **kwargs):
        """Create and authenticate a Dispatcher user. Returns the user instance."""
        from test_utils.factories.accounts import UserFactory
        kwargs.setdefault("usertype", "Dispatcher")
        user = UserFactory(**kwargs)
        self.authenticate(user)
        return user

    def deauthenticate(self):
        """Remove authentication credentials from the client."""
        self.client.credentials()
        self.user = None

    # ── HTTP shorthand ─────────────────────────────────────────────────────────

    def get(self, url, data=None, **kwargs):
        return self.client.get(url, data, **kwargs)

    def post(self, url, data=None, format="json", **kwargs):
        return self.client.post(url, data or {}, format=format, **kwargs)

    def patch(self, url, data=None, format="json", **kwargs):
        return self.client.patch(url, data or {}, format=format, **kwargs)

    def put(self, url, data=None, format="json", **kwargs):
        return self.client.put(url, data or {}, format=format, **kwargs)

    def delete(self, url, **kwargs):
        return self.client.delete(url, **kwargs)

    # ── Response status assertions ─────────────────────────────────────────────

    def assert_status(self, response, expected):
        assert response.status_code == expected, (
            f"Expected HTTP {expected}, got {response.status_code}.\nBody: {response.data if hasattr(response, 'data') else response.content}"
        )

    def assert_200(self, response): self.assert_status(response, status.HTTP_200_OK)
    def assert_201(self, response): self.assert_status(response, status.HTTP_201_CREATED)
    def assert_204(self, response): self.assert_status(response, status.HTTP_204_NO_CONTENT)
    def assert_400(self, response): self.assert_status(response, status.HTTP_400_BAD_REQUEST)
    def assert_401(self, response): self.assert_status(response, status.HTTP_401_UNAUTHORIZED)
    def assert_403(self, response): self.assert_status(response, status.HTTP_403_FORBIDDEN)
    def assert_404(self, response): self.assert_status(response, status.HTTP_404_NOT_FOUND)

    def assert_response_has_keys(self, response, *keys):
        """Assert that all given keys exist in the response body."""
        for key in keys:
            assert key in response.data, (
                f"Key '{key}' missing from response. Got: {list(response.data.keys())}"
            )

    def assert_paginated(self, response, expected_count=None):
        """Assert the response has a standard DRF paginated shape."""
        self.assert_200(response)
        assert "results" in response.data, "Response is not paginated (missing 'results')"
        if expected_count is not None:
            assert response.data["count"] == expected_count, (
                f"Expected {expected_count} items, got {response.data['count']}"
            )

    # ── DB state assertions ────────────────────────────────────────────────────

    def assert_db_state(self, model_class, pk, **field_values):
        """
        Fetch the instance fresh from the DB and assert each field value.

        Usage:
            self.assert_db_state(Transaction, txn.pk, status="completed")
        """
        instance = model_class.objects.get(pk=pk)
        for field, expected in field_values.items():
            actual = getattr(instance, field)
            assert actual == expected, (
                f"{model_class.__name__}.{field}: expected {expected!r}, got {actual!r}"
            )

    def assert_exists(self, model_class, **filters):
        """Assert that at least one matching DB record exists."""
        assert model_class.objects.filter(**filters).exists(), (
            f"Expected {model_class.__name__}.objects.filter({filters}) to exist but it does not"
        )

    def assert_not_exists(self, model_class, **filters):
        """Assert that no matching DB records exist."""
        assert not model_class.objects.filter(**filters).exists(), (
            f"Expected {model_class.__name__}.objects.filter({filters}) NOT to exist but it does"
        )
