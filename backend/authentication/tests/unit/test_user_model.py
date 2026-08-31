"""Unit tests for Authentication User model."""

from django.test import TestCase
from authentication.models import User


class UserModelUnitTest(TestCase):
    """Unit tests for custom User model attributes and string representations."""

    def test_create_user_representation(self):
        user = User(
            phone="+2348011223344",
            email="test_auth@example.com",
            contact_name="Test Auth User",
            usertype="Merchant",
        )
        self.assertEqual(str(user), "Test Auth User - (+2348011223344)")
        self.assertEqual(user.get_full_name(), "Test Auth User")
