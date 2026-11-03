"""Integration tests for LogoutView, including stopping push notifications to the device."""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import User
from dispatcher.models import Merchant, MerchantDevice


class LogoutViewIntegrationTest(TestCase):
    """Integration test suite for LogoutView."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("authentication:logout")
        self.user = User.objects.create_user(
            email="logout_merchant@example.com",
            phone="+2348099887744",
            password="StrongPassword123!",
            usertype="Merchant",
        )
        self.merchant = Merchant.objects.get(user=self.user)
        self.device = MerchantDevice.objects.create(
            merchant=self.merchant, device_id="phone-1", fcm_token="token-1"
        )
        self.other_device = MerchantDevice.objects.create(
            merchant=self.merchant, device_id="tablet-1", fcm_token="token-2"
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.refresh.access_token}")

    def _logout(self, **extra):
        return self.client.post(
            self.url, {"refresh_token": str(self.refresh), **extra}, format="json"
        )

    def _active(self, device):
        device.refresh_from_db()
        return device.is_active

    def test_logout_with_device_id_deactivates_only_that_device(self):
        response = self._logout(device_id="phone-1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertFalse(self._active(self.device))
        self.assertTrue(self._active(self.other_device))

    def test_logout_without_device_id_leaves_devices_active(self):
        response = self._logout()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self._active(self.device))
        self.assertTrue(self._active(self.other_device))

    def test_device_deactivated_even_if_refresh_token_invalid(self):
        response = self.client.post(
            self.url,
            {"refresh_token": "not-a-real-token", "device_id": "phone-1"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self._active(self.device))

    def test_cannot_deactivate_another_merchants_device(self):
        other_user = User.objects.create_user(
            email="other_merchant@example.com",
            phone="+2348099887733",
            password="StrongPassword123!",
            usertype="Merchant",
        )
        other_device = MerchantDevice.objects.create(
            merchant=Merchant.objects.get(user=other_user),
            device_id="someone-elses-phone",
            fcm_token="token-3",
        )

        self._logout(device_id="someone-elses-phone")

        self.assertTrue(self._active(other_device))

    def test_logging_in_again_reactivates_device(self):
        """Registering the device after the next login turns pushes back on."""
        self._logout(device_id="phone-1")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user).access_token}"
        )

        response = self.client.post(
            reverse("authentication:merchant_device_register"),
            {"device_id": "phone-1", "fcm_token": "token-1-new"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.device.refresh_from_db()
        self.assertTrue(self.device.is_active)
        self.assertEqual(self.device.fcm_token, "token-1-new")
