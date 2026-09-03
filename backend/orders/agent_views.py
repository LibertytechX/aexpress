"""
API views for Assured Express (AXpress) AI Agent endpoints.
Provides endpoints for:
- Quote calculation (get_quote)
- Order booking (book_order)
- Order tracking (track_order)
- Customer delivery history (get_user_deliveries)
- Payment information & virtual account details (get_payment_info)
"""

import math
import logging
import threading
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from authentication.models import User
from devs.models import ErrorLog
from dispatcher.authentication import MerchantAPIKeyAuthentication, ServiceAPIKeyAuthentication
from bot.authentication import BotAPIKeyAuthentication
from dispatcher.models import Rider
from dispatcher.utils import emit_activity
from orders.models import Delivery, Order, OrderEvent, Vehicle
from orders.pricing import calculate_effective_fare
from orders.services import get_order_service
from orders.utils import calculate_route, geocode_address
from riders.notifications import notify_rider
from sparky_utils.advice import exception_advice
from sparky_utils.exceptions import ServiceException
from sparky_utils.response import service_response
from wallet.corebanking_service import create_virtual_account
from wallet.models import Charge, VirtualAccount, Wallet

from .agent_serializers import (
    AgentBookOrderSerializer,
    CustomerDeliveriesQuerySerializer,
    QuoteRequestSerializer,
)

logger = logging.getLogger(__name__)


def _haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great-circle distance between two geographic coordinates in kilometers."""
    radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return max(0.5, round(radius_km * c, 2))


def _resolve_coordinates_and_route(
    pickup_address: str, dropoff_address: str
) -> Tuple[Dict[str, float], Dict[str, float], float, int]:
    """Geocode pickup/dropoff addresses and compute distance (km) and duration (minutes)."""
    pickup_coords = geocode_address(pickup_address)
    if not pickup_coords:
        # Lagos fallback center if geocoding returns None (e.g. In mock/test environments)
        pickup_coords = {"lat": 6.4531, "lng": 3.4244}

    dropoff_coords = geocode_address(dropoff_address)
    if not dropoff_coords:
        dropoff_coords = {"lat": 6.6018, "lng": 3.3515}

    route_data = calculate_route(origin=pickup_coords, destinations=[dropoff_coords])
    if route_data and "distance_km" in route_data and "duration_minutes" in route_data:
        distance_km = float(route_data["distance_km"])
        duration_minutes = int(route_data["duration_minutes"])
    else:
        # Defensive fallback to Haversine
        distance_km = _haversine_distance_km(
            pickup_coords["lat"],
            pickup_coords["lng"],
            dropoff_coords["lat"],
            dropoff_coords["lng"],
        )
        duration_minutes = max(10, int(round((distance_km / 25.0) * 60 + 5)))

    return pickup_coords, dropoff_coords, distance_km, duration_minutes


class OrderQuoteView(APIView):
    """
    POST /api/orders/quote/

    Calculates delivery fare estimates for a trip between pickup and delivery locations.
    Defaults to 'Bike' while also providing options for other active vehicle types.
    """

    authentication_classes = [
        ServiceAPIKeyAuthentication,
        MerchantAPIKeyAuthentication,
        BotAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.AllowAny]

    @exception_advice(model_object=ErrorLog)
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Calculate quote for the requested pickup and delivery locations."""
        serializer = QuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        pickup = data["pickup_location"]
        delivery = data["delivery_location"]
        requested_vehicle_name = data.get("vehicle", "Bike")

        _, _, distance_km, duration_minutes = _resolve_coordinates_and_route(pickup, delivery)

        # Get vehicles
        vehicles = Vehicle.objects.filter(is_active=True).order_by("base_price")
        if not vehicles.exists():
            # Fallback vehicle creation for unseeded dev environments
            vehicles = [
                Vehicle.objects.create(
                    name="Bike",
                    max_weight_kg=25,
                    base_price=Decimal("500.00"),
                    base_fare=Decimal("500.00"),
                    rate_per_km=Decimal("150.00"),
                    rate_per_minute=Decimal("10.00"),
                    min_fee=Decimal("800.00"),
                    is_active=True,
                )
            ]

        caller_user = getattr(request, "merchant", None) or (
            request.user if request.user and request.user.is_authenticated else None
        )

        quotes = []
        primary_quote = None

        for v in vehicles:
            fare = calculate_effective_fare(
                merchant_user=caller_user,
                vehicle=v,
                distance_km=distance_km,
                duration_minutes=duration_minutes,
            )
            fare_float = float(fare)
            quote_item = {
                "vehicle": v.name,
                "price": fare_float,
                "formatted_price": f"₦{fare_float:,.2f}",
                "base_fare": float(v.base_fare),
                "distance_km": round(distance_km, 2),
                "duration_minutes": duration_minutes,
            }
            quotes.append(quote_item)
            if v.name.lower() == requested_vehicle_name.lower():
                primary_quote = quote_item

        if not primary_quote and quotes:
            primary_quote = quotes[0]

        return service_response(
            status="success",
            message="Quote calculated successfully",
            data={
                "pickup_location": pickup,
                "delivery_location": delivery,
                "distance_km": round(distance_km, 2),
                "duration_minutes": duration_minutes,
                "selected_vehicle": primary_quote["vehicle"] if primary_quote else "Bike",
                "estimated_price": primary_quote["price"] if primary_quote else 0.0,
                "formatted_price": primary_quote["formatted_price"] if primary_quote else "₦0.00",
                "quotes": quotes,
            },
            status_code=status.HTTP_200_OK,
        )


class AgentBookOrderView(APIView):
    """
    POST /api/orders/agent/book/

    Creates a quick-send delivery order requested by an AI Agent.
    Automatically resolves coordinates, distance, and duration if omitted.
    """

    authentication_classes = [
        ServiceAPIKeyAuthentication,
        MerchantAPIKeyAuthentication,
        BotAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.AllowAny]

    @exception_advice(model_object=ErrorLog)
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Book a quick send order."""
        serializer = AgentBookOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Determine user / merchant
        customer_user = getattr(request, "merchant", None)
        if not customer_user and request.user and request.user.is_authenticated:
            customer_user = request.user

        sender_phone = data["sender_phone"].strip()
        if not customer_user:
            # Look up or provision user by phone
            customer_user = User.objects.filter(phone=sender_phone).first()
            if not customer_user:
                email = f"{sender_phone.replace('+', '')}@guest.axpress.net"
                customer_user = User.objects.create(
                    phone=sender_phone,
                    contact_name=data["sender_name"],
                    email=email,
                    usertype="Merchant",
                    is_active=True,
                )

        # Ensure customer has a wallet
        Wallet.objects.get_or_create(user=customer_user)

        # Vehicle
        vehicle_name = data.get("vehicle", "Bike")
        try:
            vehicle = Vehicle.objects.get(name__iexact=vehicle_name, is_active=True)
        except Vehicle.DoesNotExist:
            vehicle = Vehicle.objects.filter(is_active=True).first()
            if not vehicle:
                vehicle = Vehicle.objects.create(
                    name="Bike",
                    max_weight_kg=25,
                    base_price=Decimal("500.00"),
                    base_fare=Decimal("500.00"),
                    rate_per_km=Decimal("150.00"),
                    rate_per_minute=Decimal("10.00"),
                    min_fee=Decimal("800.00"),
                    is_active=True,
                )

        # Resolve route & distance
        pickup_coords, dropoff_coords, distance_km, duration_minutes = _resolve_coordinates_and_route(
            data["pickup_address"], data["dropoff_address"]
        )

        total_amount = calculate_effective_fare(
            merchant_user=customer_user,
            vehicle=vehicle,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
        )

        payment_method = data.get("payment_method", "wallet")
        order_service = get_order_service()

        with transaction.atomic():
            order = Order.objects.create(
                user=customer_user,
                mode="quick",
                vehicle=vehicle,
                pickup_address=data["pickup_address"],
                pickup_latitude=pickup_coords.get("lat"),
                pickup_longitude=pickup_coords.get("lng"),
                sender_name=data["sender_name"],
                sender_phone=sender_phone,
                payment_method=payment_method,
                payment_status="Pending",
                total_amount=total_amount,
                distance_km=Decimal(str(distance_km)),
                duration_minutes=duration_minutes,
                notes=data.get("notes", ""),
                scheduled_pickup_time=data.get("scheduled_pickup_time"),
                collect_on_delivery=data.get("collect_on_delivery", False),
                cod_amount=data.get("cod_amount"),
                status="Pending",
            )

            # Create Delivery record
            Delivery.objects.create(
                order=order,
                pickup_address=data["pickup_address"],
                pickup_latitude=pickup_coords.get("lat"),
                pickup_longitude=pickup_coords.get("lng"),
                sender_name=data["sender_name"],
                sender_phone=sender_phone,
                dropoff_address=data["dropoff_address"],
                receiver_name=data["receiver_name"],
                receiver_phone=data["receiver_phone"],
                package_type=data.get("package_type", "Box"),
                notes=data.get("notes", ""),
                distance_km=Decimal(str(distance_km)),
                duration_minutes=duration_minutes,
                sequence=1,
                cod_amount=data.get("cod_amount") or 0,
                status="Pending",
            )

            # Attempt payment processing if wallet
            if payment_method == "wallet":
                wallet = customer_user.wallet
                if wallet.balance >= total_amount:
                    try:
                        ok, _ = order_service.process_non_cash_payment(
                            payment_method, customer_user, order
                        )
                        if ok:
                            order.payment_status = "Paid"
                            order.save(update_fields=["payment_status"])
                    except Exception as pe:
                        logger.warning("Wallet payment auto-debit deferred: %s", pe)

        # Fire background notifications
        merchant_name = (
            getattr(customer_user, "business_name", None)
            or getattr(customer_user, "contact_name", None)
            or data["sender_name"]
        )

        def _async_notifications():
            try:
                emit_activity(
                    event_type="new_order",
                    order_id=order.order_number,
                    text=f"New agent order {order.order_number} from {merchant_name}",
                    color="gold",
                    metadata={
                        "merchant": merchant_name,
                        "amount": str(total_amount),
                        "pickup": data["pickup_address"],
                        "dropoff": data["dropoff_address"],
                    },
                )
                online_riders = Rider.objects.filter(
                    status=Rider.Status.ONLINE, is_active=True, is_authorized=True
                )
                for r in online_riders:
                    notify_rider(
                        r,
                        "New Delivery Available",
                        f"Order {order.order_number} is ready for pickup in {data['pickup_address'][:30]}",
                    )
            except Exception as e:
                logger.error("Background notification error: %s", e)

        threading.Thread(target=_async_notifications, daemon=True).start()

        return service_response(
            status="success",
            message="Order booked successfully",
            data={
                "order_number": order.order_number,
                "id": str(order.id),
                "status": order.status,
                "mode": order.mode,
                "vehicle": vehicle.name,
                "total_amount": float(total_amount),
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "pickup_address": order.pickup_address,
                "dropoff_address": data["dropoff_address"],
                "distance_km": float(distance_km),
                "duration_minutes": duration_minutes,
                "created_at": order.created_at.isoformat() if hasattr(order, "created_at") else timezone.now().isoformat(),
            },
            status_code=status.HTTP_201_CREATED,
        )


class OrderTrackView(APIView):
    """
    GET /api/orders/track/<str:order_id>/

    Retrieves order delivery status, assigned rider info, and progress timeline.
    Accepts either order_number (e.g. '6158045') or UUID id.
    """

    authentication_classes = [
        ServiceAPIKeyAuthentication,
        MerchantAPIKeyAuthentication,
        BotAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.AllowAny]

    @exception_advice(model_object=ErrorLog)
    def get(self, request: Request, order_id: str, *args: Any, **kwargs: Any) -> Response:
        """Fetch tracking details for the given order number or UUID."""
        query = Q(order_number=order_id)
        # Check if valid UUID
        try:
            import uuid
            uuid.UUID(order_id)
            query = query | Q(id=order_id)
        except (ValueError, TypeError):
            pass

        try:
            order = (
                Order.objects.select_related("vehicle", "rider", "rider__user")
                .prefetch_related("deliveries", "events")
                .get(query)
            )
        except Order.DoesNotExist:
            raise ServiceException(
                status_code=404,
                message=f"Order '{order_id}' was not found.",
            )

        # Rider details
        rider_data = None
        if order.rider:
            rider_user = getattr(order.rider, "user", None)
            rider_data = {
                "rider_id": getattr(order.rider, "rider_id", None),
                "name": getattr(rider_user, "contact_name", None) or getattr(rider_user, "full_name", "Assigned Rider"),
                "phone": getattr(rider_user, "phone", None),
                "vehicle_type": order.vehicle.name if order.vehicle else "Bike",
                "status": getattr(order.rider, "status", None),
            }

        first_delivery = order.deliveries.first()
        deliveries_data = [
            {
                "id": str(d.id),
                "dropoff_address": d.dropoff_address,
                "receiver_name": d.receiver_name,
                "receiver_phone": d.receiver_phone,
                "status": d.status,
                "sequence": d.sequence,
            }
            for d in order.deliveries.all()
        ]

        # Milestone events
        events_data = [
            {
                "event": getattr(ev, "event", getattr(ev, "event_type", "event")),
                "description": ev.description,
                "created_at": ev.created_at.isoformat(),
            }
            for ev in order.events.order_by("created_at")
        ]

        return service_response(
            status="success",
            message="Order tracking details retrieved",
            data={
                "order_number": order.order_number,
                "id": str(order.id),
                "status": order.status,
                "payment_status": order.payment_status,
                "total_amount": float(order.total_amount),
                "pickup_address": order.pickup_address,
                "sender_name": order.sender_name,
                "sender_phone": order.sender_phone,
                "dropoff_address": first_delivery.dropoff_address if first_delivery else "",
                "receiver_name": first_delivery.receiver_name if first_delivery else "",
                "receiver_phone": first_delivery.receiver_phone if first_delivery else "",
                "vehicle": order.vehicle.name if order.vehicle else "Bike",
                "rider": rider_data,
                "deliveries": deliveries_data,
                "timeline": events_data,
                "created_at": order.created_at.isoformat() if hasattr(order, "created_at") else None,
            },
            status_code=status.HTTP_200_OK,
        )


class CustomerDeliveriesView(APIView):
    """
    GET /api/orders/customer-deliveries/?phone=<phone>&limit=10&status=<status>

    Lists all active and historical deliveries associated with a customer's phone number
    (whether they are the sender or recipient).
    """

    authentication_classes = [
        ServiceAPIKeyAuthentication,
        MerchantAPIKeyAuthentication,
        BotAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.AllowAny]

    @exception_advice(model_object=ErrorLog)
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Fetch customer deliveries list."""
        serializer = CustomerDeliveriesQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        phone = params["phone"].strip()
        status_filter = params.get("status", "").strip()
        limit = params.get("limit", 10)

        # Normalize phone variations (0801..., +234801..., 234801...)
        raw_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
        clean_phone_variations = [phone, raw_phone]
        if raw_phone.startswith("234") and len(raw_phone) == 13:
            clean_phone_variations.append("0" + raw_phone[3:])
            clean_phone_variations.append("+" + raw_phone)
        elif raw_phone.startswith("0") and len(raw_phone) == 11:
            clean_phone_variations.append("234" + raw_phone[1:])
            clean_phone_variations.append("+234" + raw_phone[1:])

        phone_q = (
            Q(sender_phone__in=clean_phone_variations)
            | Q(user__phone__in=clean_phone_variations)
            | Q(deliveries__receiver_phone__in=clean_phone_variations)
        )

        queryset = (
            Order.objects.filter(phone_q)
            .select_related("vehicle", "rider__user")
            .prefetch_related("deliveries")
            .distinct()
            .order_by("-created_at")
        )

        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter)

        orders = list(queryset[:limit])

        deliveries_list = []
        for o in orders:
            first_del = o.deliveries.first()
            receiver_phone = first_del.receiver_phone if first_del else ""
            is_sender = any(p in o.sender_phone or (o.user and p in o.user.phone) for p in clean_phone_variations)
            is_receiver = any(p in receiver_phone for p in clean_phone_variations)

            role = "Sender" if is_sender else ("Receiver" if is_receiver else "Participant")

            deliveries_list.append(
                {
                    "order_number": o.order_number,
                    "id": str(o.id),
                    "role": role,
                    "status": o.status,
                    "payment_status": o.payment_status,
                    "total_amount": float(o.total_amount),
                    "vehicle": o.vehicle.name if o.vehicle else "Bike",
                    "pickup_address": o.pickup_address,
                    "dropoff_address": first_del.dropoff_address if first_del else "",
                    "sender_name": o.sender_name,
                    "receiver_name": first_del.receiver_name if first_del else "",
                    "created_at": o.created_at.isoformat() if hasattr(o, "created_at") else None,
                }
            )

        return service_response(
            status="success",
            message="Customer deliveries retrieved successfully",
            data={
                "phone": phone,
                "count": len(deliveries_list),
                "deliveries": deliveries_list,
            },
            status_code=status.HTTP_200_OK,
        )


class OrderPaymentInfoView(APIView):
    """
    GET /api/orders/<str:order_id>/payment-info/

    Retrieves payment details for an order, including the user's CoreBanking virtual account
    for bank transfer funding and settlement.
    """

    authentication_classes = [
        ServiceAPIKeyAuthentication,
        MerchantAPIKeyAuthentication,
        BotAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.AllowAny]

    @exception_advice(model_object=ErrorLog)
    def get(self, request: Request, order_id: str, *args: Any, **kwargs: Any) -> Response:
        """Fetch payment info and virtual account for an order."""
        query = Q(order_number=order_id)
        try:
            import uuid
            uuid.UUID(order_id)
            query = query | Q(id=order_id)
        except (ValueError, TypeError):
            pass

        try:
            order = Order.objects.select_related("user").get(query)
        except Order.DoesNotExist:
            raise ServiceException(
                status_code=404,
                message=f"Order '{order_id}' was not found.",
            )

        user = order.user
        wallet_balance = 0.0
        if hasattr(user, "wallet"):
            wallet_balance = float(user.wallet.balance)

        # Get or generate Virtual Account
        account_details = None
        try:
            va = VirtualAccount.objects.filter(user=user).first()
            if not va:
                va = create_virtual_account(user)

            if va:
                account_details = {
                    "account_number": getattr(va, "account_number", ""),
                    "account_name": getattr(va, "account_name", f"{user.contact_name or 'Customer'} AXPRESS"),
                    "bank_name": getattr(va, "bank_name", "Wema Bank"),
                    "bank_code": getattr(va, "bank_code", "035"),
                }
        except Exception as e:
            logger.warning("Virtual account lookup or generation error: %s", e)

        # If still no account, check order.payment_info or fallback
        if not account_details and order.payment_info and isinstance(order.payment_info, dict):
            account_details = order.payment_info

        total_amount = float(order.total_amount)
        formatted_total = f"₦{total_amount:,.2f}"

        instructions = (
            f"To complete payment for Order {order.order_number}, transfer {formatted_total} "
            f"to {account_details.get('bank_name', 'Wema Bank')} Account: {account_details.get('account_number', 'N/A')} "
            f"({account_details.get('account_name', 'Assured Express')}). Your wallet will be credited and the order processed immediately."
            if account_details
            else f"Please use an alternate payment method or contact customer support for Order {order.order_number}."
        )

        return service_response(
            status="success",
            message="Payment details retrieved successfully",
            data={
                "order_number": order.order_number,
                "id": str(order.id),
                "total_amount": total_amount,
                "formatted_total": formatted_total,
                "payment_status": order.payment_status,
                "payment_method": order.payment_method,
                "wallet_balance": wallet_balance,
                "virtual_account": account_details,
                "instructions": instructions,
            },
            status_code=status.HTTP_200_OK,
        )
