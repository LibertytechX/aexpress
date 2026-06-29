"""
Utility functions for the orders app.
Includes Google Maps integration for geocoding and route calculation.
"""

import hashlib
import requests
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache


GEOCODE_CACHE_TIMEOUT_SECONDS = 60 * 60 * 24 * 30


def _address_with_lagos_context(address: str) -> str:
    """Add stable country/state context so equivalent inputs geocode consistently."""
    cleaned_address = " ".join(address.strip().split()).rstrip(", ")
    if not cleaned_address:
        return ""

    address_lower = cleaned_address.lower()
    if "nigeria" not in address_lower:
        cleaned_address = (
            f"{cleaned_address}, Nigeria"
            if "lagos" in address_lower
            else f"{cleaned_address}, Lagos, Nigeria"
        )

    return cleaned_address


def _geocode_cache_key(address: str) -> str:
    normalized = " ".join(address.lower().split())
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"orders:geocode:{digest}"


def geocode_address(address: str) -> Optional[Dict[str, float]]:
    """
    Geocode an address using Google Maps Geocoding API.

    Appends ', Lagos, Nigeria' to the address if it does not already contain
    country context, which improves resolution for bare street addresses that
    the API cannot locate without state/country disambiguation.

    Args:
        address: The address string to geocode

    Returns:
        Dictionary with 'lat' and 'lng' keys, or None if geocoding fails
    """
    api_key = settings.GOOGLE_MAPS_API_KEY

    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not configured")

    address = _address_with_lagos_context(address)
    if not address:
        return None

    cache_key = _geocode_cache_key(address)
    try:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    except Exception:
        cached_result = None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "OK" and len(data["results"]) > 0:
            location = data["results"][0]["geometry"]["location"]
            result = {"lat": location["lat"], "lng": location["lng"]}
            try:
                cache.set(cache_key, result, timeout=GEOCODE_CACHE_TIMEOUT_SECONDS)
            except Exception:
                pass
            return result
        else:
            return None

    except Exception as e:
        print(f"Geocoding error: {str(e)}")
        return None


def calculate_route(
    origin: Dict[str, float], destinations: List[Dict[str, float]]
) -> Optional[Dict]:
    """
    Calculate route total distance and duration.

    Switches between Google Maps and custom Routing Service based on settings.

    Args:
        origin: Dictionary with 'lat' and 'lng' keys for pickup location
        destinations: List of dictionaries with 'lat' and 'lng' keys for dropoff locations

    Returns:
        Dictionary with 'distance_km' and 'duration_minutes' keys, or None if calculation fails
    """
    provider = getattr(settings, "ROUTING_PROVIDER", "google")

    if provider == "custom":
        return _calculate_route_custom(origin, destinations)
    return _calculate_route_google(origin, destinations)


def _calculate_route_custom(
    origin: Dict[str, float], destinations: List[Dict[str, float]]
) -> Optional[Dict]:
    """
    Calculate route using the custom Go-based routing service.
    """
    service_url = getattr(settings, "ROUTING_SERVICE_URL", "")
    api_key = getattr(settings, "ROUTING_SERVICE_API_KEY", "")

    if not service_url:
        print("ROUTING_SERVICE_URL not configured, falling back to Google")
        return _calculate_route_google(origin, destinations)

    if not destinations:
        return {"distance_km": 0.0, "duration_minutes": 0}

    # OSRM expects lng,lat
    origin_str = f"{origin['lng']},{origin['lat']}"
    destinations_list = [f"{p['lng']},{p['lat']}" for p in destinations]

    params = {
        "origin": origin_str,
        "destinations": destinations_list,
    }
    headers = {"X-API-Key": api_key}

    try:
        response = requests.get(service_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success" and data.get("data"):
            # OSRM returns distance in meters and duration in seconds
            # We take the first route from the list
            route = data["data"][0]
            total_distance_meters = route["distance"]
            total_duration_seconds = route["duration"]

            distance_km = round(total_distance_meters / 1000, 2)
            duration_minutes = round(total_duration_seconds / 60, 0)

            return {
                "distance_km": distance_km,
                "duration_minutes": int(duration_minutes),
            }
        else:
            print(f"Custom routing service error: {data.get('message')}")
            return None

    except Exception as e:
        print(f"Custom route calculation error: {str(e)}")
        return None


def _calculate_route_google(
    origin: Dict[str, float], destinations: List[Dict[str, float]]
) -> Optional[Dict]:
    """
    Calculate route total distance and duration using Google Maps Distance Matrix API.
    """
    api_key = settings.GOOGLE_MAPS_API_KEY

    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not configured")

    if not destinations:
        return {"distance_km": 0.0, "duration_minutes": 0}

    # Build sequence of points: origin -> destinations[0] -> destinations[1] -> ... -> destinations[-1]
    points = [origin] + destinations

    # We want distances for: points[0]->points[1], points[1]->points[2], ..., points[n-1]->points[n]
    # By passing all sources as origins and all targets as destinations,
    # we can pick out the diagonal elements of the resulting matrix.
    origins = points[:-1]
    targets = points[1:]

    origins_str = "|".join([f"{p['lat']},{p['lng']}" for p in origins])
    destinations_str = "|".join([f"{p['lat']},{p['lng']}" for p in targets])

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origins_str,
        "destinations": destinations_str,
        "key": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "OK":
            total_distance_meters = 0
            total_duration_seconds = 0

            # data['rows'] contains the results for each origin
            # For each step i, we want the distance from origins[i] to targets[i]
            for i in range(len(origins)):
                elements = data["rows"][i]["elements"]
                # The targets were passed in the same order, so elements[i] corresponds to targets[i]
                element = elements[i]

                if element.get("status") == "OK":
                    total_distance_meters += element["distance"]["value"]
                    total_duration_seconds += element["duration"]["value"]
                else:
                    return None  # Unreachable route or other error for this leg

            distance_km = round(total_distance_meters / 1000, 2)
            duration_minutes = round(total_duration_seconds / 60, 0)

            return {
                "distance_km": distance_km,
                "duration_minutes": int(duration_minutes),
            }
        else:
            return None

    except Exception as e:
        print(f"Google route calculation error: {str(e)}")
        return None


