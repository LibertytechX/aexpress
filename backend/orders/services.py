"""
Order service integrations.

This module contains third-party logistics integrations used within the orders
application. Currently includes the SmartPercel locker-delivery integration.
"""

import logging
from typing import Any, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SMARTPARCEL_BASE_URL: str = getattr(
    settings,
    "SMARTPARCEL_BASE_URL",
    "https://sandboxapi.smartparcel.ng/v2/business/",
)

SMARTPARCEL_PUBLIC_KEY: str = getattr(
    settings,
    "SMARTPARCEL_PUBLIC_KEY",
    "9FbIeKhNkQmTpWsYv2y5A8D0GcJfLiOlRnUqXtZw3y6B9EaHdK",
)

SMARTPARCEL_SECRET_KEY: str = getattr(
    settings,
    "SMARTPARCEL_SECRET_KEY",
    "Yv2y5A8DaGcJfMiOlRoUqXtZw3z6B9EbHdKgNjPmSoVrYu1x4A",
)

# Connection / read timeout in seconds
_DEFAULT_TIMEOUT: tuple[int, int] = (10, 30)


# ---------------------------------------------------------------------------
# SmartPercelIntegration
# ---------------------------------------------------------------------------


class SmartPercelIntegration:
    """Client wrapper for the SmartParcel V2 Business API.

    All methods use POST as required by the SmartParcel V2 Business API, and
    authentication (apikey) is sent within the JSON request body.

    Discovery: Core/Geography endpoints require the Public Key as 'apikey',
    while Business/Parcel endpoints require the Secret Key.

    Attributes:
        base_url: Root URL for the SmartParcel API.
        public_key: Business public key used for Core/Geography endpoints.
        secret_key: Business secret key used for Business/Parcel endpoints.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ) -> None:
        self.base_url: str = (base_url or SMARTPARCEL_BASE_URL).rstrip("/") + "/"
        self.public_key: str = public_key or SMARTPARCEL_PUBLIC_KEY
        self.secret_key: str = secret_key or SMARTPARCEL_SECRET_KEY

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _headers(self) -> dict[str, str]:
        """Build the common request headers for SmartParcel."""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _post(
        self, path: str, payload: Optional[dict] = None, use_public_key: bool = False
    ) -> tuple[bool, Any]:
        """Perform a POST request against the SmartParcel API.

        Automatically injects the appropriate 'apikey' into the payload.
        """
        url = f"{self.base_url}{path.lstrip('/')}"
        data = payload or {}
        data["apikey"] = self.public_key if use_public_key else self.secret_key

        try:
            response = requests.post(
                url,
                headers=self._headers,
                json=data,
                timeout=_DEFAULT_TIMEOUT,
            )
            print("status code: ", response.status_code)
            return self._parse(response)
        except requests.exceptions.Timeout:
            logger.error("SmartParcel API timeout — POST %s", url)
            return False, "Request to SmartParcel timed out. Please try again."
        except requests.exceptions.ConnectionError:
            logger.error("SmartParcel API connection error — POST %s", url)
            return False, "Could not connect to SmartParcel. Check network settings."
        except Exception as exc:  # noqa: BLE001
            logger.exception("SmartParcel unexpected error — POST %s: %s", url, exc)
            return False, f"Unexpected error: {exc}"

    @staticmethod
    def _parse(response: requests.Response) -> tuple[bool, Any]:
        """Parse an HTTP response from the SmartParcel API."""
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}

        if response.ok:
            return True, body

        message = (
            body.get("message")
            or body.get("error")
            or body.get("detail")
            or f"SmartParcel error {response.status_code}"
        )
        logger.warning(
            "SmartParcel API non-2xx — %s %s: %s",
            response.status_code,
            response.url,
            message,
        )
        return False, message

    # ------------------------------------------------------------------
    # Geography
    # ------------------------------------------------------------------

    def list_states(self) -> tuple[bool, Any]:
        """Retrieve all states where SmartParcel operates (Uses Public Key)."""
        return self._post("states/", use_public_key=True)

    def list_cities_by_state(self, state_id: str) -> tuple[bool, Any]:
        """Retrieve cities for a specific state (Uses Public Key)."""
        return self._post("cities/state/", {"stateid": state_id}, use_public_key=True)

    # ------------------------------------------------------------------
    # Boxes
    # ------------------------------------------------------------------

    def list_boxes_by_city(self, city_id: str) -> tuple[bool, Any]:
        """Retrieve SmartParcel boxes in a specific city (Uses Public Key)."""
        return self._post("boxes/city/", {"cityid": city_id}, use_public_key=True)

    def get_box_details(self, box_id: str) -> tuple[bool, Any]:
        """Retrieve details of a single SmartParcel box (Uses Public Key)."""
        return self._post("boxes/info/", {"boxid": box_id}, use_public_key=True)

    def list_locker_sizes(self) -> tuple[bool, Any]:
        """Retrieve all available locker sizes (Uses Public Key)."""
        return self._post("sizes/", use_public_key=True)

    # ------------------------------------------------------------------
    # Parcels
    # ------------------------------------------------------------------

    def create_parcel(self, payload: dict) -> tuple[bool, Any]:
        """Create a new parcel on the network (Uses Secret Key)."""
        return self._post("parcels/create/", payload, use_public_key=False)

    def get_parcel_details(self, tracking_number: str) -> tuple[bool, Any]:
        """Retrieve details of a parcel by tracking number (Uses Secret Key)."""
        return self._post(
            "parcels/info/all/",
            {"parceldetailid": tracking_number},
            use_public_key=False,
        )

    def cancel_parcel(self, tracking_number: str) -> tuple[bool, Any]:
        """Cancel an existing parcel (Uses Secret Key)."""
        return self._post(
            "parcels/cancel/",
            {"parceldetailid": tracking_number},
            use_public_key=False,
        )
