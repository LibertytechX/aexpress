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

    Args:
        address: The address string to geocode

    Returns:
        Dictionary with 'lat' and 'lng' keys, or None if geocoding fails
    """
    api_key = settings.GOOGLE_MAPS_API_KEY

    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not configured")

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
    Calculate route distance and duration using Google Maps Directions API.

    Args:
        origin: Dictionary with 'lat' and 'lng' keys for pickup location
        destinations: List of dictionaries with 'lat' and 'lng' keys for dropoff locations

    Returns:
        Dictionary with 'distance_km' and 'duration_minutes' keys, or None if calculation fails
    """
    api_key = settings.GOOGLE_MAPS_API_KEY

    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not configured")

    # Format origin
    origin_str = f"{origin['lat']},{origin['lng']}"

    # Format destination (last point in the route)
    destination_str = f"{destinations[-1]['lat']},{destinations[-1]['lng']}"

    # Format waypoints (all points except the last one)
    waypoints = []
    if len(destinations) > 1:
        for dest in destinations[:-1]:
            waypoints.append(f"{dest['lat']},{dest['lng']}")

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': origin_str,
        'destination': destination_str,
        'key': api_key,
        'optimize': 'true'  # Optimize waypoint order
    }

    if waypoints:
        params['waypoints'] = 'optimize:true|' + '|'.join(waypoints)

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'OK' and len(data['routes']) > 0:
            route = data['routes'][0]

            # Sum up all legs
            total_distance_meters = 0
            total_duration_seconds = 0

            for leg in route['legs']:
                total_distance_meters += leg['distance']['value']
                total_duration_seconds += leg['duration']['value']

            # Convert to km and minutes
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

