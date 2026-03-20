"""
Utility functions for the orders app.
Includes Google Maps integration for geocoding and route calculation.
"""

import requests
from typing import Dict, List, Tuple, Optional
from django.conf import settings


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

    # Append location context if not already present so that bare street names
    # resolve correctly (mirrors the Stack Overflow fix for Distance Matrix API).
    address_lower = address.lower()
    if 'nigeria' not in address_lower and 'lagos' not in address_lower:
        address = address.rstrip(', ') + ', Lagos, Nigeria'

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': api_key
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'OK' and len(data['results']) > 0:
            location = data['results'][0]['geometry']['location']
            return {
                'lat': location['lat'],
                'lng': location['lng']
            }
        else:
            return None

    except Exception as e:
        print(f"Geocoding error: {str(e)}")
        return None


def calculate_route(origin: Dict[str, float], destinations: List[Dict[str, float]]) -> Optional[Dict]:
    """
    Calculate route total distance and duration using Google Maps Distance Matrix API.

    Args:
        origin: Dictionary with 'lat' and 'lng' keys for pickup location
        destinations: List of dictionaries with 'lat' and 'lng' keys for dropoff locations

    Returns:
        Dictionary with 'distance_km' and 'duration_minutes' keys, or None if calculation fails
    """
    api_key = settings.GOOGLE_MAPS_API_KEY

    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not configured")

    if not destinations:
        return {'distance_km': 0.0, 'duration_minutes': 0}

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
        'origins': origins_str,
        'destinations': destinations_str,
        'key': api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'OK':
            total_distance_meters = 0
            total_duration_seconds = 0

            # data['rows'] contains the results for each origin
            # For each step i, we want the distance from origins[i] to targets[i]
            for i in range(len(origins)):
                elements = data['rows'][i]['elements']
                # The targets were passed in the same order, so elements[i] corresponds to targets[i]
                element = elements[i]

                if element.get('status') == 'OK':
                    total_distance_meters += element['distance']['value']
                    total_duration_seconds += element['duration']['value']
                else:
                    return None  # Unreachable route or other error for this leg

            distance_km = round(total_distance_meters / 1000, 2)
            duration_minutes = round(total_duration_seconds / 60, 0)

            return {
                'distance_km': distance_km,
                'duration_minutes': int(duration_minutes)
            }
        else:
            return None

    except Exception as e:
        print(f"Route calculation error: {str(e)}")
        return None

