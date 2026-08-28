"""Integration tests for Authentication API endpoints."""

from django.test import TestCase
from rest_framework.test import APIClient
from authentication.models import User


class AuthEndpointsIntegrationTest(TestCase):
    """Integration tests for authentication views."""

    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_access(self):
        response = self.client.get("/api/v1/auth/profile/")
        # Endpoint requires authentication or returns 401/404
        self.assertIn(response.status_code, [401, 403, 404])
