import logging
from celery import shared_task
from decimal import Decimal
from django.db import transaction
from .models import Order
from riders.models import OrderOffer
from wallet.models import Charge

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_order_proximity(self, order_id):
    """
    Background task to geocode an order's pickup address,
    find the closest zone, and create an OrderOffer.
    """
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"process_order_proximity: Order {order_id} not found.")
        return False

    # 1. Geocode pickup address if coordinates are missing
    if order.pickup_latitude is None or order.pickup_longitude is None:
        from .utils import geocode_address

        try:
            coords = geocode_address(order.pickup_address)
            if coords:
                order.pickup_latitude = coords["lat"]
                order.pickup_longitude = coords["lng"]
                # Save coordinates
                Order.objects.filter(id=order_id).update(
                    pickup_latitude=order.pickup_latitude,
                    pickup_longitude=order.pickup_longitude,
                )
        except Exception as e:
            logger.error(
                f"process_order_proximity: Geocoding failed for Order {order.order_number}: {e}"
            )
            # We can still proceed if we have a fallback or if coordinates were partially provided

    # 2. Find closest zone
    from dispatcher.utils import find_closest_zone

    zone = None
    if order.pickup_latitude is not None and order.pickup_longitude is not None:
        try:
            zone = find_closest_zone(order.pickup_latitude, order.pickup_longitude)
        except Exception as e:
            logger.error(
                f"process_order_proximity: find_closest_zone failed for Order {order.order_number}: {e}"
            )

    # 3. Calculate estimated earnings (using commission_pct from SystemSettings)
    from dispatcher.models import SystemSettings

    settings = SystemSettings.objects.first()
    commission_factor = (
        Decimal(str(settings.commission_pct / 100)) if settings else Decimal("0.2")
    )

    total_amount = Decimal(str(order.total_amount or 0))
    estimated_earnings = (total_amount * commission_factor).quantize(Decimal("0.01"))

    # 4. Create OrderOffer
    dedicated_rider = None
    merchant_profile = getattr(order.user, "merchant_profile", None)
    if merchant_profile:
        from subscriptions.services import get_dedicated_rider
        from dispatcher.models import Rider

        dedicated_rider = get_dedicated_rider(merchant_profile)
        # Check if rider is online (or on delivery but still dedicated)
        if dedicated_rider and dedicated_rider.status == Rider.Status.OFFLINE:
            dedicated_rider = None

    try:
        with transaction.atomic():
            # Check if an offer already exists for this order to avoid duplicates on retries
            offer, created = OrderOffer.objects.get_or_create(
                order=order,
                defaults={
                    "rider": dedicated_rider,
                    "status": OrderOffer.Status.PENDING,
                    "estimated_earnings": estimated_earnings,
                    "zone": zone,
                },
            )
            # TODO: update the order rider
            if not created:
                # Update existing offer if it was created without a zone
                if zone and not offer.zone:
                    offer.zone = zone
                    offer.save(update_fields=["zone"])

            logger.info(
                f"process_order_proximity: OrderOffer created/updated for {order.order_number} in zone {zone}"
            )
            return True
    except Exception as e:
        logger.error(
            f"process_order_proximity: Failed to create OrderOffer for {order.order_number}: {e}"
        )
        raise self.retry(exc=e)


@shared_task
def create_order_charge(order_id):
    try:
        order = Order.objects.get(id=order_id)
        charge = Charge.objects.create(
            user=order.user,
            order=order,
            amount=order.total_amount,
            status="pending",
        )
        return charge
    except Exception as e:
        logger.error(
            f"create_order_charge: Failed to create charge for Order {order_id}: {e}"
        )
