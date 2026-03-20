import os
import requests


def main(args):
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "body": {"success": False, "error": "GOOGLE_MAPS_API_KEY not configured"}
        }

    origin = args.get("origin")
    destinations = args.get("destinations", [])

    if not origin or not destinations:
        return {
            "body": {
                "success": False,
                "error": "Both origin and destinations are required",
            }
        }

    try:
        origins_str = f"{origin['lat']},{origin['lng']}"
        destinations_str = "|".join([f"{p['lat']},{p['lng']}" for p in destinations])
    except KeyError:
        return {
            "body": {
                "success": False,
                "error": "Origin and destinations must contain 'lat' and 'lng' keys",
            }
        }

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
            max_distance_meters = 0
            max_duration_seconds = 0
            valid_destinations_found = False

            elements = data["rows"][0]["elements"]

            for element in elements:
                if element.get("status") == "OK":
                    valid_destinations_found = True
                    dist = element["distance"]["value"]
                    dur = element["duration"]["value"]

                    if dist > max_distance_meters:
                        max_distance_meters = dist
                    if dur > max_duration_seconds:
                        max_duration_seconds = dur

            if valid_destinations_found:
                max_distance_km = round(max_distance_meters / 1000, 2)
                max_duration_minutes = int(round(max_duration_seconds / 60, 0))

                return {
                    "body": {
                        "success": True,
                        "distance_km": max_distance_km,
                        "duration_minutes": max_duration_minutes,
                    }
                }
            else:
                return {
                    "body": {
                        "success": False,
                        "error": "Route not found for any of the given destinations.",
                    }
                }
        else:
            return {
                "body": {
                    "success": False,
                    "error": data.get("error_message", "Google Maps API error"),
                }
            }

    except Exception as e:
        return {"body": {"success": False, "error": str(e)}}
