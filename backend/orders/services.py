"""
Order service integrations.

This module contains third-party logistics integrations used within the orders
application. Currently includes the SmartPercel locker-delivery integration.
"""

from orders.models import Order
from devs.utils.advice import log_exception_advice
import logging
from typing import Any, Optional
from wallet.models import Charge, Wallet
from wallet.escrow import EscrowManager

import requests
from django.conf import settings
from abc import ABC, abstractmethod
from typing import Tuple
from subscriptions.services import (
    get_active_postpaid_subscription,
    process_order_subscription,
    accumulate_postpaid_order,
)
from decimal import Decimal
import uuid

from sparky_utils.exceptions import ServiceException

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

    def list_assigned_boxes(self) -> tuple[bool, Any]:
        """Retrieve the list of boxes assigned to the merchant (Uses Public Key)."""
        return self._post("boxes/assigned/", use_public_key=True)

    # ------------------------------------------------------------------
    # Parcels
    # ------------------------------------------------------------------

    def list_pending_pickups(self) -> tuple[bool, Any]:
        """Retrieve the list of parcels ready for pickup (Uses Public Key in sandbox)."""
        return self._post("pendingpickups/", use_public_key=True)

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

    # ------------------------------------------------------------------
    # Simulation (Sandbox only)
    # ------------------------------------------------------------------

    def simulate_drop_parcel(self, box_id: str, unlock_code: str) -> tuple[bool, Any]:
        """Simulate dropping a parcel into a SmartParcel locker box.

        This is a sandbox-only endpoint used to trigger the "dropped" state
        transition so that downstream collect-code flows can be tested end-to-end.

        Args:
            box_id: The ID of the SmartParcel box.
            unlock_code: The unlock code for dropping the parcel.

        Returns:
            Tuple of (success: bool, data: Any).
        """
        return self._post(
            "locker/dropparcel/",
            {"boxid": box_id, "unlockcode": unlock_code},
            use_public_key=True,
        )

    def simulate_collect_parcel(
        self, box_id: str, unlock_code: str
    ) -> tuple[bool, Any]:
        """Simulate a recipient collecting a parcel from a SmartParcel locker.

        This is a sandbox-only endpoint used to trigger the "collected" state
        transition so that the full pickup workflow can be tested end-to-end.

        Args:
            box_id: The ID of the SmartParcel box.
            unlock_code: The unlock code for collecting the parcel.

        Returns:
            Tuple of (success: bool, data: Any).
        """
        return self._post(
            "locker/collectparcel/",
            {"boxid": box_id, "unlockcode": unlock_code},
            use_public_key=True,
        )


# order service contracts/interface


class OrderService(ABC):
    """
    Order Service contracts for all order service implementations
    """

    @abstractmethod
    def process_parcel_delivery(
        self,
        is_pickup: bool,
        is_delivery: bool,
        request_data: dict,
        parcel_payload: dict = None,
    ) -> Tuple[bool, Any]:
        """
        Process a parcel delivery.

        Args:
            is_pickup: Whether the parcel is for pickup from a locker.
            is_delivery: Whether the parcel is for delivery to a locker.
            request_data: The original order request data.
            parcel_payload: The payload for creating a new parcel (if is_delivery).

        Returns:
            Tuple of (success: bool, response_dict: dict).
            The response_dict contains:
                - message: Error message if success is False.
                - status_code: HTTP status code.
                - parcel_info: Dictionary containing parcel/tracking information.
                - pickup_address: Updated pickup address from locker details.
                - dropoff_address: Updated dropoff address from locker details.
        """
        pass

    @abstractmethod
    def process_non_cash_payment(
        self, payment_method: str, request_user: any, order: Order
    ) -> Tuple[bool, Any]:
        """
        Process non-cash payment for an order.
        such as subscription payment, wallet payment, and postpaid payment, escow charge
        """
        pass

    @abstractmethod
    def create_dispatcher_order(self, request_user: any, validated_data: dict) -> Order:
        """
        Create an order from the dispatcher dashboard.
        """
        pass

    @abstractmethod
    def process_partners_order(self, order: Order, data: dict) -> Order:
        """
        Process partner-specific order fields.
        """
        pass


class IOrderService(OrderService):
    """
    Implementation of the order service contracts
    """

    @log_exception_advice(app_name="create_percel_order")
    def process_parcel_delivery(
        self,
        is_pickup: bool,
        is_delivery: bool,
        request_data: dict,
        parcel_payload: dict = None,
    ) -> Tuple[bool, Any]:
        """
        Implementation of the parcel delivery processing.

        Args:
            is_pickup (bool): True if picking up from a SmartParcel locker.
            is_delivery (bool): True if delivering to a SmartParcel locker.
            request_data (dict): Validated request data from the view.
            parcel_payload (dict, optional): Payload for creating a new parcel. Defaults to None.

        Returns:
            Tuple[bool, Any]: (Success, Response dictionary)
        """
        response = {
            "message": "",
            "status_code": 400,
            "parcel_info": None,
            "pickup_address": request_data.get("pickup_address"),
            "dropoff_address": request_data.get("dropoff_address"),
        }
        smartparcel_service = SmartPercelIntegration()

        if is_pickup:
            ok, list_response = smartparcel_service.list_pending_pickups()
            if not ok:
                response["message"] = str(list_response)
                return False, response

            parcels = list_response.get("parcels", [])
            box_number = request_data.get("collect_code")
            if not box_number:
                response["message"] = "Box number is required for parcel pickup"
                return False, response

            found_parcel = next(
                (p for p in parcels if p["boxlockernumber"] == box_number), None
            )
            if not found_parcel:
                response["message"] = f"Parcel not found for box number: {box_number}"
                response["status_code"] = 404
                return False, response

            response["parcel_info"] = found_parcel
            response["pickup_address"] = found_parcel.get(
                "boxaddress", response["pickup_address"]
            )

        if is_delivery:
            box_id = request_data.get("box_id")
            ok, delivery_response = smartparcel_service.get_box_details(box_id)
            if not ok:
                response["message"] = "Parcel order service not available"
                response["status_code"] = 503
                return False, response

            box_data = delivery_response.get("data") or delivery_response
            response["dropoff_address"] = (
                box_data.get("boxaddress")
                or box_data.get("address")
                or response["dropoff_address"]
            )

            # Create a new parcel integration record
            ok, create_response = smartparcel_service.create_parcel(parcel_payload)
            if not ok:
                response["message"] = (
                    create_response
                    if isinstance(create_response, str)
                    else "Failed to create parcel"
                )
                response["status_code"] = 503
                return False, response

            response["parcel_info"] = create_response

        return True, response

    @log_exception_advice(app_name="non_cash_payment")
    def process_non_cash_payment(
        self, payment_method: str, request_user: any, order: Order
    ) -> Tuple[bool, Any]:
        """
        Process non-cash payment for an order.
        such as subscription payment, wallet payment, and postpaid payment, escow charge
        """
        response = {"message": "", "status_code": 200}
        match payment_method:
            case "subscription":
                subscription = process_order_subscription(order)
                if not subscription:
                    response["message"] = "Failed to process subscription payment"
                    response["status_code"] = 400
                    # clear the order
                    order.delete()
                    return False, response

                return True, {}
            case "wallet":
                charges = Charge.objects.filter(
                    user=request_user, status="pending", is_active=True
                )
                if charges.exists():
                    order.delete()
                    response["message"] = (
                        "Failed to process wallet payment, you have pending charges 🔥"
                    )
                    response["status_code"] = 400
                    return False, response
                wallet = Wallet.objects.filter(user=request_user)
                if wallet.count() == 0:
                    # create the wallet
                    wallet = Wallet.objects.create(user=request_user)
                    order.delete()
                    response["message"] = "Wallet not found"
                    response["status_code"] = 404
                    return False, response
                wallet = wallet.first()
                try:
                    EscrowManager.hold_funds(
                        wallet=wallet,
                        amount=order.total_amount,
                        order_number=order.order_number,
                        description=f"Escrow hold for Quick Send order #{order.order_number}",
                    )
                    order.escrow_held = True
                    order.save()
                except ValueError as e:
                    response["message"] = str(e)
                    response["status_code"] = 400
                    order.delete()
                    return False, response
                return True, response
            case "postpaid":
                merchant_profile = getattr(request_user, "merchant_profile", None)
                if not merchant_profile:
                    response["message"] = "Merchant profile not found"
                    response["status_code"] = 400
                    # clear the order
                    order.delete()
                    return False, response
                postpaid_sub = get_active_postpaid_subscription(merchant_profile)
                if not postpaid_sub:
                    response["message"] = "Postpaid subscription not found"
                    response["status_code"] = 400
                    # clear the order
                    order.delete()
                    return False, response
                if postpaid_sub.status == "blocked":
                    response["message"] = "Postpaid subscription is blocked"
                    response["status_code"] = 400
                    # clear the order
                    order.delete()
                    return False, response
                accumulated = accumulate_postpaid_order(postpaid_sub, order)
                if not accumulated:
                    response["message"] = "Failed to accumulate postpaid order"
                    response["status_code"] = 400
                    # clear the order
                    order.delete()
                    return False, response
                return True, response
            case (
                _
            ):  # payment method not any of the cases above such as cash_on_delivery and receivers pay
                return True, {}

    @log_exception_advice(app_name="create_dispatcher_order")
    def create_dispatcher_order(self, request_user: any, validated_data: dict) -> Order:
        """
        Implementation of dispatcher order creation.
        """
        from orders.models import Delivery, Vehicle
        from dispatcher.models import Rider, Merchant as MerchantProfile
        from orders.utils import geocode_address
        from orders.pricing import calculate_effective_fare

        # Extract fields
        pickup = validated_data.get("pickup")
        dropoff = validated_data.get("dropoff")
        pickup_lat = validated_data.get("pickup_lat")
        pickup_lng = validated_data.get("pickup_lng")
        dropoff_lat = validated_data.get("dropoff_lat")
        dropoff_lng = validated_data.get("dropoff_lng")
        is_relay_order = validated_data.get("is_relay_order", False)
        sender_name = validated_data.get("senderName")
        sender_phone = validated_data.get("senderPhone")
        receiver_name = validated_data.get("receiverName")
        receiver_phone = validated_data.get("receiverPhone")
        vehicle_name = validated_data.get("vehicle")
        package_type = validated_data.get("packageType")
        price = validated_data.get("price")
        manual_price = bool(validated_data.get("manual_price"))
        rider_id = (validated_data.get("riderId", "") or "").strip()
        merchant_id = (validated_data.get("merchantId", "") or "").strip()
        distance_km = validated_data.get("distance_km")
        duration_minutes = validated_data.get("duration_minutes")
        is_partner_order = validated_data.get("is_partner_order", False)
        partner_order_count = validated_data.get("partner_order_count")

        # Resolve User (Merchant or Request User)
        order_user = request_user
        merchant_profile = None
        if merchant_id:
            merchant_profile = MerchantProfile.objects.filter(
                merchant_id=merchant_id
            ).first()
            if merchant_profile:
                order_user = merchant_profile.user
        else:
            merchant_profile = getattr(order_user, "merchant_profile", None)

        # Resolve Vehicle
        vehicle_obj = Vehicle.objects.filter(name__iexact=vehicle_name).first()
        if not vehicle_obj:
            vehicle_obj = Vehicle.objects.first()

        # Partner Constraints & Price Calculation
        if is_partner_order:
            if not merchant_profile or not merchant_profile.is_partner:
                raise ServiceException(
                    status_code=400, message="Merchant is not a partner"
                )

            if not merchant_profile.partner_base_price:
                raise ServiceException(
                    status_code=400,
                    message="Partner base price is not set for this merchant",
                )

            if not partner_order_count:
                raise ServiceException(
                    status_code=400,
                    message="partner_order_count is required for partner orders",
                )
            # TODO: Add partner pricing logic
            if manual_price and price is not None:
                total_amount = price
            else:
                total_amount = merchant_profile.partner_base_price * partner_order_count

            # Default values for missing data
            pickup = pickup or "Partner Pickup"
            dropoff = dropoff or "Partner Delivery"
            sender_name = sender_name or (
                getattr(order_user, "business_name", "")
                or order_user.contact_name
                or order_user.phone
            )
            sender_phone = sender_phone or order_user.phone
            receiver_name = receiver_name or "Partner Receiver"
            receiver_phone = receiver_phone or "0000000000"
            distance_km = distance_km or 0
            duration_minutes = duration_minutes or 0
            package_type = package_type or "Box"
        else:
            # Calculate Price for regular orders
            if manual_price and price is not None:
                total_amount = price
            else:
                total_amount = calculate_effective_fare(
                    order_user,
                    vehicle_obj,
                    distance_km or 0,
                    duration_minutes or 0,
                )

            def _coords_missing(lat, lng):
                return lat is None or lng is None

            # Best-effort geocoding fallback
            if _coords_missing(pickup_lat, pickup_lng) and pickup:
                geo = geocode_address(pickup)
                if geo:
                    pickup_lat = geo.get("lat")
                    pickup_lng = geo.get("lng")

            if _coords_missing(dropoff_lat, dropoff_lng) and dropoff:
                geo = geocode_address(dropoff)
                if geo:
                    dropoff_lat = geo.get("lat")
                    dropoff_lng = geo.get("lng")

        try:
            total_amount = Decimal(str(total_amount)).quantize(Decimal("0.01"))
        except Exception:
            pass

        # Resolve Rider
        rider_obj = None
        if rider_id:

            def _is_uuid(val: str) -> bool:
                try:
                    uuid.UUID(str(val))
                    return True
                except (ValueError, AttributeError, TypeError):
                    return False

            if _is_uuid(rider_id):
                rider_obj = Rider.objects.filter(id=rider_id).first()
                if not rider_obj:
                    rider_obj = Rider.objects.filter(rider_id=rider_id).first()
            else:
                rider_obj = Rider.objects.filter(rider_id=rider_id).first()

        # Create Order
        order = Order.objects.create(
            user=order_user,
            pickup_address=pickup,
            pickup_latitude=pickup_lat,
            pickup_longitude=pickup_lng,
            sender_name=sender_name,
            sender_phone=sender_phone,
            vehicle=vehicle_obj,
            total_amount=total_amount,
            rider=rider_obj,
            dispatcher_assigned=True if rider_obj else False,
            source="dispatcher_web",
            status="Assigned" if rider_obj else "Pending",
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            is_relay_order=is_relay_order,
            routing_status=(
                Order.RoutingStatus.PENDING
                if is_relay_order
                else Order.RoutingStatus.READY
            ),
        )

        # Create Delivery
        Delivery.objects.create(
            order=order,
            pickup_address=pickup,
            pickup_latitude=pickup_lat,
            pickup_longitude=pickup_lng,
            sender_name=sender_name,
            sender_phone=sender_phone,
            dropoff_address=dropoff,
            dropoff_latitude=dropoff_lat,
            dropoff_longitude=dropoff_lng,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            package_type=package_type,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
        )

        # Partner processing
        if validated_data.get("is_partner_order"):
            self.process_partners_order(order, validated_data)

        # Post-creation tasks
        payment_method = validated_data.get("payment_method")
        if payment_method in ["cash", "cash_on_pickup", "receiver_pays"]:
            from orders.tasks import create_order_charge

            create_order_charge.delay(order.id)

        return order

    def process_partners_order(self, order: Order, data: dict) -> Order:
        """
        Process partner-specific order fields.
        """
        order.is_partner_order = True
        order.partner_order_count = data.get("partner_order_count")
        order.file_uploaded_urls = data.get("file_uploaded_urls", [])
        order.save()
        return order


def get_order_service() -> OrderService:
    return IOrderService()
