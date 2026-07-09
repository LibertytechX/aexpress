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
from orders.utils import aws_place_autocomplete, aws_place_details, aws_reverse_geocode


class PlacesAutocompleteView(APIView):
    """API endpoint to get place suggestions using AWS Location Service.

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

        suggestions = aws_place_autocomplete(query)
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
    """API endpoint to reverse geocode coordinates using AWS Location Service.

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
