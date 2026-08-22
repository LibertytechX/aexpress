"""
Utility functions for the orders app.
Includes Google Maps integration for geocoding and route calculation.
"""

import hashlib
import requests
import boto3
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

        if data.get("status") == "OK" and len(data.get("results", [])) > 0:
            location = data["results"][0]["geometry"]["location"]
            result = {"lat": location["lat"], "lng": location["lng"]}
            try:
                cache.set(cache_key, result, timeout=GEOCODE_CACHE_TIMEOUT_SECONDS)
            except Exception:
                pass
            return result
        else:
            result = _geocode_fallback(address)
            if result:
                try:
                    cache.set(cache_key, result, timeout=GEOCODE_CACHE_TIMEOUT_SECONDS)
                except Exception:
                    pass
                return result
            return None

    except Exception as e:
        print(f"Geocoding error: {str(e)}")
        result = _geocode_fallback(address)
        if result:
            try:
                cache.set(cache_key, result, timeout=GEOCODE_CACHE_TIMEOUT_SECONDS)
            except Exception:
                pass
            return result
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


def get_aws_location_client():
    """Get AWS Location client."""
    return boto3.client(
        "location",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=getattr(settings, "AWS_S3_REGION_NAME", "us-east-1"),
    )


def aws_geocode_address(address: str) -> Optional[Dict[str, float]]:
    """Geocode address using AWS Location Service search_place_index_for_text."""
    try:
        client = get_aws_location_client()
        place_index = getattr(
            settings, "AWS_LOCATION_PLACE_INDEX", "aexpress-place-index"
        )
        response = client.search_place_index_for_text(
            IndexName=place_index,
            Text=address,
            FilterCountries=["NGA"],
            MaxResults=1,
        )
        results = response.get("Results", [])
        if results:
            point = results[0]["Place"]["Geometry"]["Point"]
            return {"lat": point[1], "lng": point[0]}
    except Exception as e:
        print(f"AWS Geocoding error: {str(e)}")
    return None


def aws_place_autocomplete(query: str, max_results: int = 8) -> List[Dict]:
    """Get place suggestions using AWS Location Service search_place_index_for_suggestions."""
    try:
        client = get_aws_location_client()
        place_index = getattr(
            settings, "AWS_LOCATION_PLACE_INDEX", "aexpress-place-index"
        )

        response = client.search_place_index_for_suggestions(
            IndexName=place_index,
            Text=query,
            FilterCountries=["NGA"],
            BiasPosition=[3.3792, 6.5244],  # Bias towards Lagos
            MaxResults=max_results,
        )

        results = response.get("Results", [])
        suggestions = []
        for res in results:
            text = res.get("Text", "")
            place_id = res.get("PlaceId", "")

            # Extract main/secondary text similar to Google's structured_formatting
            parts = text.split(",", 1)
            main_text = parts[0].strip()
            secondary_text = parts[1].strip() if len(parts) > 1 else ""

            suggestions.append(
                {
                    "place_id": place_id,
                    "description": text,
                    "is_aws": True,
                    "structured_formatting": {
                        "main_text": main_text,
                        "secondary_text": secondary_text,
                    },
                }
            )
        return suggestions
    except Exception as e:
        print(f"AWS Autocomplete error: {str(e)}")
        return []


def aws_place_details(place_id: str) -> Optional[Dict]:
    """Get place details using AWS Location Service get_place."""
    try:
        client = get_aws_location_client()
        place_index = getattr(
            settings, "AWS_LOCATION_PLACE_INDEX", "aexpress-place-index"
        )
        response = client.get_place(
            IndexName=place_index,
            PlaceId=place_id,
        )
        place = response.get("Place", {})
        if place:
            point = place.get("Geometry", {}).get("Point", [])
            if len(point) == 2:
                return {
                    "formatted_address": place.get("Label", ""),
                    "lat": point[1],
                    "lng": point[0],
                }
    except Exception as e:
        print(f"AWS Place Details error: {str(e)}")
    return None


def aws_reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """Reverse geocode coordinates using AWS Location Service search_place_index_for_position."""
    try:
        client = get_aws_location_client()
        place_index = getattr(
            settings, "AWS_LOCATION_PLACE_INDEX", "aexpress-place-index"
        )
        response = client.search_place_index_for_position(
            IndexName=place_index,
            Position=[lng, lat],  # [longitude, latitude]
            MaxResults=1,
        )
        results = response.get("Results", [])
        if results:
            return results[0]["Place"].get("Label", "")
    except Exception as e:
        print(f"AWS Reverse Geocoding error: {str(e)}")
    return None


def geoapify_place_autocomplete(query: str) -> List[Dict]:
    """Get location autocomplete suggestions from Geoapify."""
    api_key = getattr(settings, "GEOAPIFY_API_KEY", "")
    if not api_key:
        return []

    # Bias to Lagos, Nigeria if not present
    lower = query.lower()
    search_query = (
        query if "lagos" in lower or "nigeria" in lower else f"{query}, Lagos, Nigeria"
    )

    url = "https://api.geoapify.com/v1/geocode/autocomplete"
    params = {
        "text": search_query,
        "filter": "countrycode:ng",
        "bias": "rect:2.70,6.25,3.95,6.75",
        "limit": 5,
        "format": "json",
        "apiKey": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        suggestions = []
        for result in data.get("results", []):
            place_id = result.get("place_id")
            formatted = result.get("formatted", "")

            # Extract main/secondary formatting
            parts = [p.strip() for p in formatted.split(",")]
            main_text = parts[0] if parts else formatted
            secondary_text = ", ".join(parts[1:]) if len(parts) > 1 else ""

            suggestions.append(
                {
                    "place_id": f"geoapify:{place_id}",
                    "description": formatted,
                    "is_geoapify": True,
                    "lat": result.get("lat"),
                    "lng": result.get("lon"),
                    "structured_formatting": {
                        "main_text": main_text,
                        "secondary_text": secondary_text,
                    },
                }
            )
        return suggestions
    except Exception as e:
        print(f"[Geoapify Autocomplete] Error: {str(e)}")
        return []


def geoapify_place_details(place_id: str) -> Optional[Dict]:
    """Retrieve details for a Geoapify place ID."""
    api_key = getattr(settings, "GEOAPIFY_API_KEY", "")
    if not api_key:
        return None

    url = "https://api.geoapify.com/v2/place-details"
    params = {
        "id": place_id,
        "apiKey": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])
        if not features:
            return None

        properties = features[0].get("properties", {})
        formatted = properties.get("formatted")
        lat = properties.get("lat")
        lng = properties.get("lon")

        if formatted and lat is not None and lng is not None:
            return {
                "formatted_address": formatted,
                "lat": lat,
                "lng": lng,
            }
        return None
    except Exception as e:
        print(f"[Geoapify Details] Error: {str(e)}")
        return None


def geoapify_geocode_address(address: str) -> Optional[Dict[str, float]]:
    """Geocode address string to lat/lng coordinates using Geoapify."""
    api_key = getattr(settings, "GEOAPIFY_API_KEY", "")
    if not api_key:
        return None

    lower = address.lower()
    search_query = (
        address
        if "lagos" in lower or "nigeria" in lower
        else f"{address}, Lagos, Nigeria"
    )

    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text": search_query,
        "filter": "countrycode:ng",
        "limit": 1,
        "format": "json",
        "apiKey": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return None

        lat = results[0].get("lat")
        lng = results[0].get("lon")

        if lat is not None and lng is not None:
            return {
                "lat": lat,
                "lng": lng,
            }
        return None
    except Exception as e:
        print(f"[Geoapify Geocode] Error: {str(e)}")
        return None


def geoapify_reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """Reverse geocode coordinates using Geoapify."""
    api_key = getattr(settings, "GEOAPIFY_API_KEY", "")
    if not api_key:
        return None

    url = "https://api.geoapify.com/v1/geocode/reverse"
    params = {
        "lat": lat,
        "lon": lng,
        "format": "json",
        "apiKey": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if results:
            return results[0].get("formatted")
        return None
    except Exception as e:
        print(f"[Geoapify Reverse Geocode] Error: {str(e)}")
        return None


def _geocode_fallback(address: str) -> Optional[Dict[str, float]]:
    """Helper to try Geoapify geocode, then fallback to AWS geocode."""
    geoapify_key = getattr(settings, "GEOAPIFY_API_KEY", "")
    if geoapify_key:
        result = geoapify_geocode_address(address)
        if result:
            return result
    return aws_geocode_address(address)


def mapbox_place_autocomplete(
    query: str, session_token: Optional[str] = None
) -> List[Dict]:
    """Get location autocomplete suggestions from Mapbox Geocoding v6 API.

    Args:
        query: The partial search query string.
        session_token: Optional UUID session token.

    Returns:
        List of dictionaries with normalized location suggestions containing lat/lng.
    """
    api_key: str = getattr(settings, "MAPBOX_ACCESS_TOKEN", "")
    if not api_key:
        return []

    url = "https://api.mapbox.com/search/geocode/v6/forward"
    params = {
        "q": query,
        "country": "ng",
        "proximity": "3.3792,6.5244",  # Bias towards Lagos
        "autocomplete": "true",
        "limit": 5,
        "access_token": api_key,
    }
    if session_token:
        params["session_token"] = str(session_token)

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        suggestions: List[Dict] = []
        for feature in data.get("features", []):
            properties = feature.get("properties", {})
            mapbox_id = properties.get("mapbox_id") or feature.get("id", "")
            name = properties.get("name", "")
            place_formatted = properties.get("place_formatted", "")
            full_address = properties.get("full_address") or f"{name}, {place_formatted}"

            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [])

            suggestion_dict = {
                "place_id": f"mapbox:{mapbox_id}",
                "description": full_address,
                "is_mapbox": True,
                "structured_formatting": {
                    "main_text": name,
                    "secondary_text": place_formatted,
                },
            }

            if len(coordinates) == 2:
                suggestion_dict["lat"] = coordinates[1]
                suggestion_dict["lng"] = coordinates[0]

            suggestions.append(suggestion_dict)
        return suggestions
    except Exception as e:
        try:
            print("Error Response: ", response.json())
        except Exception:
            pass
        print(f"[Mapbox Geocoding Autocomplete] Error: {str(e)}")
        return []


def mapbox_place_details(
    place_id: str, session_token: Optional[str] = None
) -> Optional[Dict]:
    """Retrieve details for a Mapbox place ID using Search Box Retrieve API.

    Args:
        place_id: The Mapbox feature ID (without prefix).
        session_token: Optional UUID session token used in autocomplete step.

    Returns:
        Dictionary containing formatted address, lat, and lng, or None.
    """
    api_key: str = getattr(settings, "MAPBOX_ACCESS_TOKEN", "")
    if not api_key:
        return None

    url = f"https://api.mapbox.com/search/searchbox/v1/retrieve/{place_id}"
    params = {
        "access_token": api_key,
    }
    if session_token:
        params["session_token"] = str(session_token)

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])
        if not features:
            return None

        properties = features[0].get("properties", {})
        geometry = features[0].get("geometry", {})
        coordinates = geometry.get("coordinates", [])

        full_address = properties.get("full_address") or properties.get("name", "")

        if len(coordinates) == 2:
            return {
                "formatted_address": full_address,
                "lat": coordinates[1],
                "lng": coordinates[0],
            }
        return None
    except Exception as e:
        print(f"[Mapbox Details] Error: {str(e)}")
        return None


def mapbox_reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """Reverse geocode coordinates using the Mapbox Geocoding v6 API."""
    api_key: str = getattr(settings, "MAPBOX_ACCESS_TOKEN", "")
    if not api_key:
        return None

    url = "https://api.mapbox.com/search/geocode/v6/reverse"
    params = {
        "longitude": lng,
        "latitude": lat,
        "access_token": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        features = response.json().get("features", [])
        if not features:
            return None

        properties = features[0].get("properties", {})
        return (
            properties.get("full_address")
            or properties.get("place_formatted")
            or properties.get("name")
        )
    except Exception as e:
        print(f"[Mapbox Reverse Geocode] Error: {str(e)}")
        return None
