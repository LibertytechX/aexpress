import os
import logging
import time
import math
import secrets
from decimal import Decimal, ROUND_HALF_UP

import requests
from celery import shared_task
from django.conf import settings
from .models import Rider
from .utils import MailgunEmailService

logger = logging.getLogger(__name__)


_RELAY_NODES_CACHE = {"ts": 0.0, "nodes": None}
_RELAY_NODES_TTL_SECONDS = 300


def _haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance in KM."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _get_active_relay_nodes_cached():
    from .models import RelayNode

    now = time.time()
    if (
        _RELAY_NODES_CACHE["nodes"] is not None
        and (now - _RELAY_NODES_CACHE["ts"]) < _RELAY_NODES_TTL_SECONDS
    ):
        return _RELAY_NODES_CACHE["nodes"]

    nodes = list(
        RelayNode.objects.filter(is_active=True)
        .select_related("zone")
        .only("id", "name", "latitude", "longitude", "zone")
    )
    _RELAY_NODES_CACHE["nodes"] = nodes
    _RELAY_NODES_CACHE["ts"] = now
    return nodes


def _directions_legs(origin, points):
    """Return list of (distance_km, duration_minutes) between origin->points[0]->..."""
    api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
    if not api_key:
        return None

    if not points:
        return []

    origin_str = f"{origin['lat']},{origin['lng']}"
    destination_str = f"{points[-1]['lat']},{points[-1]['lng']}"
    waypoints = points[:-1]

    params = {
        "origin": origin_str,
        "destination": destination_str,
        "key": api_key,
    }
    if waypoints:
        params["waypoints"] = "|".join([f"{p['lat']},{p['lng']}" for p in waypoints])

    # 1-hour cache for identical waypoint chains
    try:
        from django.core.cache import cache

        cache_key = "relay_route_legs:" + "->".join(
            [origin_str] + [f"{p['lat']},{p['lng']}" for p in points]
        )
        cached = cache.get(cache_key)
        if cached:
            return cached
    except Exception:
        cache_key = None

    url = "https://maps.googleapis.com/maps/api/directions/json"
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "OK" or not data.get("routes"):
        return None

    legs = data["routes"][0].get("legs") or []
    out = []
    for leg in legs:
        d_km = (leg["distance"]["value"] or 0) / 1000.0
        t_min = int(round((leg["duration"]["value"] or 0) / 60.0))
        out.append((round(d_km, 2), t_min))

    if cache_key:
        try:
            from django.core.cache import cache

            cache.set(cache_key, out, timeout=3600)
        except Exception:
            pass

    return out


def _estimate_legs_haversine(origin, points):
    if not points:
        return []
    prev = origin
    out = []
    for p in points:
        d = _haversine_km(prev["lat"], prev["lng"], p["lat"], p["lng"])
        # simple Lagos ETA heuristic: 4 mins per km
        out.append((round(d, 2), int(max(1, round(d * 4)))))
        prev = p
    return out


def _build_greedy_relay_hops(pickup, dropoff, max_leg_km_est=90.0, max_hops=12):
    """Greedy hop selection using haversine distance as a cheap proxy."""
    nodes = _get_active_relay_nodes_cached()
    direct = _haversine_km(pickup["lat"], pickup["lng"], dropoff["lat"], dropoff["lng"])

    # Filter nodes roughly "near" the pickup→dropoff corridor (triangle inequality)
    filtered = []
    for n in nodes:
        if n.latitude is None or n.longitude is None:
            continue
        d1 = _haversine_km(pickup["lat"], pickup["lng"], float(n.latitude), float(n.longitude))
        d2 = _haversine_km(float(n.latitude), float(n.longitude), dropoff["lat"], dropoff["lng"])
        if (d1 + d2) <= (direct * 1.6):
            filtered.append(n)

    hops = []
    cur = pickup
    remaining = _haversine_km(cur["lat"], cur["lng"], dropoff["lat"], dropoff["lng"])

    while remaining > max_leg_km_est:
        best = None
        best_remaining = None
        for n in filtered:
            n_lat, n_lng = float(n.latitude), float(n.longitude)
            leg = _haversine_km(cur["lat"], cur["lng"], n_lat, n_lng)
            if leg > max_leg_km_est:
                continue
            rem = _haversine_km(n_lat, n_lng, dropoff["lat"], dropoff["lng"])
            # must make progress
            if rem >= remaining - 1.0:
                continue
            if best is None or rem < best_remaining:
                best = n
                best_remaining = rem

        if not best:
            break

        hops.append(best)
        cur = {"lat": float(best.latitude), "lng": float(best.longitude)}
        remaining = best_remaining

        if len(hops) >= max_hops:
            break

    # If still far and we couldn't hop, signal failure by returning None
    if _haversine_km(cur["lat"], cur["lng"], dropoff["lat"], dropoff["lng"]) > max_leg_km_est:
        return None
    return hops


@shared_task
def send_onboarding_email_task(email, first_name, password, rider_id=None):
    """
    Background task to send onboarding email.
    """
    try:
        # Send onboarding email
        MailgunEmailService.send_onboarding_email(email, first_name, password)

        if rider_id:
            logger.info(f"Onboarding email sent for rider {rider_id}")
        else:
            logger.info(f"Onboarding email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Error in send_onboarding_email_task: {str(e)}")
        return False


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def upload_rider_documents_to_s3(
    self,
    rider_id,
    avatar_data=None,
    avatar_name=None,
    vehicle_photo_data=None,
    vehicle_photo_name=None,
    driving_license_photo_data=None,
    driving_license_photo_name=None,
    identity_card_photo_data=None,
    identity_card_photo_name=None,
):
    """
    Background task to upload rider documents to S3.
    """
    import base64
    import io
    from .s3_utils import upload_image_file_to_s3

    try:
        rider = Rider.objects.get(id=rider_id)

        # Upload Avatar
        if avatar_data and avatar_name:
            file_content = base64.b64decode(avatar_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(file_obj, avatar_name, "riders/avatars")
            if url:
                rider.avatar = url

        # Upload Vehicle Photo
        if vehicle_photo_data and vehicle_photo_name:
            file_content = base64.b64decode(vehicle_photo_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(
                file_obj, vehicle_photo_name, "riders/vehicles"
            )
            if url:
                rider.vehicle_photo = url

        # Upload License
        if driving_license_photo_data and driving_license_photo_name:
            file_content = base64.b64decode(driving_license_photo_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(
                file_obj, driving_license_photo_name, "riders/license"
            )
            if url:
                rider.driving_license_photo = url

        # Upload ID Card
        if identity_card_photo_data and identity_card_photo_name:
            file_content = base64.b64decode(identity_card_photo_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(
                file_obj, identity_card_photo_name, "riders/id_card"
            )
            if url:
                rider.identity_card_photo = url

        rider.save()
        logger.info(f"Successfully uploaded documents for rider {rider_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to upload documents for rider {rider_id}: {str(e)}")
        return False


def generate_relay_legs_sync(order_id):
    """Generate relay legs synchronously for a relay order (called directly by the view)."""
    from django.db import transaction
    from orders.models import Order, OrderLeg
    from orders.utils import geocode_address
    from .utils import emit_activity

    try:
        with transaction.atomic():
            order = (
                Order.objects.select_for_update(of=("self",))
                .prefetch_related("deliveries")
                .get(id=order_id)
            )

            if not order.is_relay_order:
                return True

            first_delivery = order.deliveries.first()
            if not first_delivery:
                order.routing_status = Order.RoutingStatus.FAILED
                order.routing_error = "No delivery dropoff found for this order."
                order.save(update_fields=["routing_status", "routing_error"])
                return False

            # Coordinates (prefer provided lat/lng; fallback to geocode)
            pickup = {
                "lat": order.pickup_latitude,
                "lng": order.pickup_longitude,
            }
            if pickup["lat"] is None or pickup["lng"] is None:
                try:
                    g = geocode_address(order.pickup_address)
                except Exception:
                    g = None
                if not g:
                    order.routing_status = Order.RoutingStatus.FAILED
                    order.routing_error = "Pickup coordinates missing and geocoding failed."
                    order.save(update_fields=["routing_status", "routing_error"])
                    return False
                pickup = g
                order.pickup_latitude = pickup["lat"]
                order.pickup_longitude = pickup["lng"]

            dropoff = {
                "lat": first_delivery.dropoff_latitude,
                "lng": first_delivery.dropoff_longitude,
            }
            if dropoff["lat"] is None or dropoff["lng"] is None:
                try:
                    g = geocode_address(first_delivery.dropoff_address)
                except Exception:
                    g = None
                if not g:
                    order.routing_status = Order.RoutingStatus.FAILED
                    order.routing_error = "Dropoff coordinates missing and geocoding failed."
                    order.save(update_fields=["routing_status", "routing_error"])
                    return False
                dropoff = g
                first_delivery.dropoff_latitude = dropoff["lat"]
                first_delivery.dropoff_longitude = dropoff["lng"]

            # Build hop chain (2-pass: tighter hops if road legs exceed cap)
            hop_nodes = (
                _build_greedy_relay_hops(pickup, dropoff, max_leg_km_est=90.0)
                or _build_greedy_relay_hops(pickup, dropoff, max_leg_km_est=80.0)
            )
            if hop_nodes is None:
                order.routing_status = Order.RoutingStatus.FAILED
                order.routing_error = "Could not find relay hops to keep legs within 100km."
                order.save(update_fields=["routing_status", "routing_error"])
                emit_activity(
                    event_type="relay_route_failed",
                    order_id=order.order_number,
                    text=f"Relay routing failed for {order.order_number}",
                    color="red",
                    metadata={"reason": order.routing_error},
                )
                return False

            # Points for routing legs: hop coords + final dropoff
            points = [
                {"lat": float(n.latitude), "lng": float(n.longitude)} for n in hop_nodes
            ] + [dropoff]

            legs_metrics = None
            try:
                legs_metrics = _directions_legs(pickup, points)
            except Exception as exc:
                logger.warning(f"generate_relay_legs_task: directions failed: {exc}")

            if legs_metrics is None:
                legs_metrics = _estimate_legs_haversine(pickup, points)

            # Enforce 100km cap (best-effort; haversine fallback may exceed in real roads)
            if any(d > 100.0 for d, _ in legs_metrics):
                order.routing_status = Order.RoutingStatus.FAILED
                order.routing_error = "One or more legs exceed 100km after routing validation."
                order.save(update_fields=["routing_status", "routing_error"])
                emit_activity(
                    event_type="relay_route_failed",
                    order_id=order.order_number,
                    text=f"Relay route exceeds cap for {order.order_number}",
                    color="red",
                    metadata={"reason": order.routing_error},
                )
                return False

            # Clear and recreate legs (idempotent retries)
            order.legs.all().delete()

            created_legs = []
            prev_node = None
            for idx, (dist_km, dur_min) in enumerate(legs_metrics, start=1):
                next_node = hop_nodes[idx - 1] if idx - 1 < len(hop_nodes) else None
                leg = OrderLeg.objects.create(
                    order=order,
                    leg_number=idx,
                    start_relay_node=prev_node,
                    end_relay_node=next_node,
                    hub_pin=f"{secrets.randbelow(1000000):06d}",
                    distance_km=float(dist_km or 0),
                    duration_minutes=int(dur_min or 0),
                )
                created_legs.append(leg)
                prev_node = next_node

            # Settlement: distance-weighted split of 80% of order total
            total_distance = sum(float(l.distance_km or 0) for l in created_legs) or 0.0
            total_pool = (order.total_amount or Decimal("0")) * Decimal("0.8")
            if total_distance > 0:
                for leg in created_legs:
                    share = Decimal(str(float(leg.distance_km) / total_distance))
                    payout = (total_pool * share).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    leg.rider_payout = payout
                    leg.save(update_fields=["rider_payout"])

            # Suggest rider for first leg
            try:
                riders = Rider.objects.filter(
                    is_authorized=True,
                    status=Rider.Status.ONLINE,
                    current_latitude__isnull=False,
                    current_longitude__isnull=False,
                )
                best = None
                best_d = None
                for r in riders[:200]:
                    d = _haversine_km(
                        float(pickup["lat"]),
                        float(pickup["lng"]),
                        float(r.current_latitude),
                        float(r.current_longitude),
                    )
                    if best is None or d < best_d:
                        best, best_d = r, d
                order.suggested_rider = best
            except Exception:
                order.suggested_rider = None

            # Persist computed totals + status
            order.relay_legs_count = len(created_legs)
            order.distance_km = round(sum(d for d, _ in legs_metrics), 2)
            order.duration_minutes = int(sum(t for _, t in legs_metrics))
            order.routing_status = Order.RoutingStatus.READY
            order.routing_error = ""
            order.save(
                update_fields=[
                    "pickup_latitude",
                    "pickup_longitude",
                    "relay_legs_count",
                    "distance_km",
                    "duration_minutes",
                    "routing_status",
                    "routing_error",
                    "suggested_rider",
                ]
            )
            first_delivery.save(update_fields=["dropoff_latitude", "dropoff_longitude"])

        emit_activity(
            event_type="relay_route_ready",
            order_id=order.order_number,
            text=f"Relay route ready for {order.order_number} ({order.relay_legs_count} legs)",
            color="green",
            metadata={
                "legs": order.relay_legs_count,
                "suggested_rider_id": str(order.suggested_rider.id)
                if order.suggested_rider
                else None,
            },
        )
        return True

    except Exception as exc:
        logger.exception(f"generate_relay_legs_sync failed for order {order_id}: {exc}")
        try:
            from orders.models import Order
            from .utils import emit_activity

            Order.objects.filter(id=order_id).update(
                routing_status=Order.RoutingStatus.FAILED,
                routing_error=str(exc),
            )
            order = Order.objects.filter(id=order_id).first()
            if order:
                emit_activity(
                    event_type="relay_route_failed",
                    order_id=order.order_number,
                    text=f"Relay routing failed for {order.order_number}",
                    color="red",
                    metadata={"error": str(exc)},
                )
        except Exception:
            pass
        return False
