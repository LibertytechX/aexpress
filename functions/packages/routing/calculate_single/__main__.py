import os
import requests


def main(args):
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "body": {"success": False, "error": "GOOGLE_MAPS_API_KEY not configured"}
        }

    origin = args.get("origin")
    destination = args.get("destination")

    # Also support a list of single destinations (e.g., destinations=[drop]) from the payload
    # since views.py typically uses destinations arrays
    destinations_list = args.get("destinations")
    if not destination and destinations_list and len(destinations_list) > 0:
        destination = destinations_list[0]

    if not origin or not destination:
        return {
            "body": {
                "success": False,
                "error": "Both origin and destination are required",
            }
        }

    try:
        origins_str = f"{origin['lat']},{origin['lng']}"
        destinations_str = f"{destination['lat']},{destination['lng']}"
    except KeyError:
        return {
            "body": {
                "success": False,
                "error": "Origin and destination must contain 'lat' and 'lng' keys",
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
            element = data["rows"][0]["elements"][0]
            if element.get("status") == "OK":
                distance_meters = element["distance"]["value"]
                duration_seconds = element["duration"]["value"]

                distance_km = round(distance_meters / 1000, 2)
                duration_minutes = int(round(duration_seconds / 60, 0))

                return {
                    "body": {
                        "success": True,
                        "distance_km": distance_km,
                        "duration_minutes": duration_minutes,
                    }
                }
            else:
                return {
                    "body": {
                        "success": False,
                        "error": "Route not found for the given locations.",
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
