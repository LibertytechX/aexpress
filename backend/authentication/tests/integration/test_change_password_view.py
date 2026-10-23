"""Integration tests for ChangePasswordView endpoint."""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from authentication.models import User


class ChangePasswordViewIntegrationTest(TestCase):
    """Integration test suite for ChangePasswordView."""

    OLD_PASSWORD = "OldPassword123!"
    NEW_PASSWORD = "NewPassword456!"

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("authentication:change_password")
        self.login_url = reverse("authentication:login")
        self.user = User.objects.create_user(
            email="change_password@example.com",
            phone="+2348099887755",
            password=self.OLD_PASSWORD,
            contact_name="Change Password User",
            business_name="Change Password Logistics",
        )
        self.client.force_authenticate(user=self.user)

    def _change(self, old=OLD_PASSWORD, new=NEW_PASSWORD, confirm=NEW_PASSWORD):
        return self.client.post(
            self.url,
            {"old_password": old, "new_password": new, "confirm_password": confirm},
            format="json",
        )

    def _password_unchanged(self):
        self.user.refresh_from_db()
        return self.user.check_password(self.OLD_PASSWORD)

    def test_change_password_success(self):
        """Valid request changes the password and returns 200."""
        response = self._change()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Password changed successfully!")

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.NEW_PASSWORD))
        self.assertFalse(self.user.check_password(self.OLD_PASSWORD))

    def test_login_works_with_new_password_only(self):
        """After a change, login accepts the new password and rejects the old one."""
        self._change()
        anon = APIClient()

        new_login = anon.post(
            self.login_url,
            {"phone": "08099887755", "password": self.NEW_PASSWORD},
            format="json",
        )
        old_login = anon.post(
            self.login_url,
            {"phone": "08099887755", "password": self.OLD_PASSWORD},
            format="json",
        )

        self.assertEqual(new_login.status_code, status.HTTP_200_OK)
        self.assertEqual(old_login.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_fields(self):
        """Any missing field returns 400 and leaves the password unchanged."""
        for payload in (
            {},
            {"old_password": self.OLD_PASSWORD},
            {"old_password": self.OLD_PASSWORD, "new_password": self.NEW_PASSWORD},
            {"new_password": self.NEW_PASSWORD, "confirm_password": self.NEW_PASSWORD},
        ):
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(
                    response.data["error"],
                    "Old password, new password, and confirm password are required.",
                )
        self.assertTrue(self._password_unchanged())

    def test_passwords_do_not_match(self):
        response = self._change(confirm="Different789!")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Passwords do not match")
        self.assertTrue(self._password_unchanged())

    def test_new_password_too_short(self):
        response = self._change(new="abc", confirm="abc")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "Password must be at least 6 characters long"
        )
        self.assertTrue(self._password_unchanged())

    def test_incorrect_current_password(self):
        response = self._change(old="WrongPassword!")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Current password is incorrect.")
        self.assertTrue(self._password_unchanged())

    def test_new_password_same_as_old(self):
        response = self._change(new=self.OLD_PASSWORD, confirm=self.OLD_PASSWORD)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "New password must be different from the current password.",
        )
        self.assertTrue(self._password_unchanged())

    def test_unauthenticated_request_rejected(self):
        """Without a token the endpoint returns 401 and changes nothing."""
        response = APIClient().post(
            self.url,
            {
                "old_password": self.OLD_PASSWORD,
                "new_password": self.NEW_PASSWORD,
                "confirm_password": self.NEW_PASSWORD,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(self._password_unchanged())
