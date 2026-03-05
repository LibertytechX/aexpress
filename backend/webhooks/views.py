from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Webhook
from .serializers import WebhookSerializer


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

    def post(self, request):
        event_name = request.data.get("event_name")
        if not event_name:
            return Response(
                {
                    "success": False,
                    "errors": {"event_name": ["This field is required."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        event_name = event_name.lower()

        # Try to get existing webhook for this event
        try:
            webhook = Webhook.objects.get(event_name=event_name)
            serializer = WebhookSerializer(webhook, data=request.data, partial=True)
        except Webhook.DoesNotExist:
            serializer = WebhookSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": f"Webhook for '{event_name}' configured successfully.",
                    "data": serializer.data,
                },
                status=(
                    status.HTTP_201_CREATED
                    if "webhook" not in locals()
                    else status.HTTP_200_OK
                ),
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
