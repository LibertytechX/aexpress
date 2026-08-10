from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Webhook
from .serializers import WebhookSerializer
from sparky_utils.advice import exception_advice
from sparky_utils.exceptions import ServiceException
from sparky_utils.response import service_response


class WebhookCreateUpdateView(APIView):
    """
    API endpoint to create or update a webhook configuration.
    POST /api/webhooks/config/
    {
        "event_name": "order-created",
        "url": "https://example.com/webhook",
        "secret_key": "my-secret-key"
    }
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice()
    def post(self, request):
        # check if the request from a merchant
        if not request.user.is_merchant:
            raise ServiceException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Only merchants can create webhooks.",
            )

        merchant = request.user.merchant_profile

        # Try to get existing webhook for this event
        serializer = WebhookSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(merchant=merchant)
            return service_response(
                status="success",
                data=serializer.data,
                message="Webhook configured successfully!",
                status_code=201,
            )

        return service_response(
            status="error",
            data=serializer.errors,
            message="Webhook configuration failed!",
            status_code=400,
        )
