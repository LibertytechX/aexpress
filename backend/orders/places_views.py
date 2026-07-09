from typing import Any
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.settings import api_settings
from rest_framework.request import Request
from rest_framework.response import Response
from dispatcher.authentication import MerchantAPIKeyAuthentication
from devs.models import ErrorLog
from sparky_utils.advice import exception_advice
from sparky_utils.response import service_response
from django.conf import settings
from orders.utils import (
    aws_place_autocomplete,
    aws_place_details,
    aws_reverse_geocode,
    aws_geocode_address,
    geoapify_place_autocomplete,
    geoapify_place_details,
    geoapify_reverse_geocode,
    geoapify_geocode_address,
)


class PlacesAutocompleteView(APIView):
    """API endpoint to get place suggestions using AWS Location or Geoapify.

    GET /api/orders/places/autocomplete/?q=...
    """

    authentication_classes = [
        MerchantAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle place autocomplete suggestions query.

        Args:
            request: The incoming request containing 'q' parameter.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Service response with normalized place suggestions.
        """
        query: str = request.query_params.get("q", "")
        if not query:
            return service_response(
                status="error",
                message="Query parameter 'q' is required",
                data=[],
                status_code=400,
            )

        geoapify_key = getattr(settings, "GEOAPIFY_API_KEY", "")
        if geoapify_key:
            suggestions = geoapify_place_autocomplete(query)
            if suggestions:
                return service_response(
                    status="success",
                    message="Autocomplete suggestions retrieved successfully",
                    data=suggestions,
                    status_code=200,
                )

        # Fallback to AWS
        suggestions = aws_place_autocomplete(query)
        for s in suggestions:
            s["place_id"] = f"aws:{s['place_id']}"
            s["is_aws"] = True

        return service_response(
            status="success",
            message="Autocomplete suggestions retrieved successfully",
            data=suggestions,
            status_code=200,
        )


class PlaceDetailsView(APIView):
    """API endpoint to get details of a place by PlaceId.

    GET /api/orders/places/details/?place_id=...
    """

    authentication_classes = [
        MerchantAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle place details query by Place ID.

        Args:
            request: The incoming request containing 'place_id' parameter.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Service response with formatted address and coordinates.
        """
        place_id: str = request.query_params.get("place_id", "")
        if not place_id:
            return service_response(
                status="error",
                message="Query parameter 'place_id' is required",
                data={},
                status_code=400,
            )

        if place_id.startswith("geoapify:"):
            real_id = place_id.split(":", 1)[1]
            details = geoapify_place_details(real_id)
        elif place_id.startswith("aws:"):
            real_id = place_id.split(":", 1)[1]
            details = aws_place_details(real_id)
        else:
            # Backward compatibility / fallback: try Geoapify first if configured, else AWS
            geoapify_key = getattr(settings, "GEOAPIFY_API_KEY", "")
            if geoapify_key:
                details = geoapify_place_details(place_id)
            else:
                details = None
            if not details:
                details = aws_place_details(place_id)

        if not details:
            return service_response(
                status="error",
                message="Place details not found",
                data={},
                status_code=404,
            )

        return service_response(
            status="success",
            message="Place details retrieved successfully",
            data=details,
            status_code=200,
        )


class ReverseGeocodeView(APIView):
    """API endpoint to reverse geocode coordinates.

    GET /api/orders/places/reverse-geocode/?lat=...&lng=...
    """

    authentication_classes = [
        MerchantAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle reverse geocoding request.

        Args:
            request: The incoming request containing 'lat' and 'lng' parameters.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Service response with the resolved address string.
        """
        lat_str: str = request.query_params.get("lat", "")
        lng_str: str = request.query_params.get("lng", "")
        if not lat_str or not lng_str:
            return service_response(
                status="error",
                message="Query parameters 'lat' and 'lng' are required",
                data={},
                status_code=400,
            )

        try:
            lat = float(lat_str)
            lng = float(lng_str)
        except ValueError:
            return service_response(
                status="error",
                message="Latitude and longitude must be valid float numbers",
                data={},
                status_code=400,
            )

        geoapify_key = getattr(settings, "GEOAPIFY_API_KEY", "")
        if geoapify_key:
            address = geoapify_reverse_geocode(lat, lng)
        else:
            address = None

        if not address:
            address = aws_reverse_geocode(lat, lng)

        if not address:
            return service_response(
                status="error",
                message="Could not reverse geocode coordinates",
                data={},
                status_code=404,
            )

        return service_response(
            status="success",
            message="Coordinates reverse geocoded successfully",
            data={"address": address},
            status_code=200,
        )


class GeocodeView(APIView):
    """API endpoint to geocode an address string.

    GET /api/orders/places/geocode/?address=...
    """

    authentication_classes = [
        MerchantAPIKeyAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle geocoding request.

        Args:
            request: The incoming request containing 'address' parameter.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Service response with coordinates.
        """
        address: str = request.query_params.get("address", "")
        if not address:
            return service_response(
                status="error",
                message="Query parameter 'address' is required",
                data={},
                status_code=400,
            )

        geoapify_key = getattr(settings, "GEOAPIFY_API_KEY", "")
        if geoapify_key:
            coords = geoapify_geocode_address(address)
        else:
            coords = None

        if not coords:
            coords = aws_geocode_address(address)

        if not coords:
            return service_response(
                status="error",
                message="Could not geocode address",
                data={},
                status_code=404,
            )

        return service_response(
            status="success",
            message="Address geocoded successfully",
            data=coords,
            status_code=200,
        )
