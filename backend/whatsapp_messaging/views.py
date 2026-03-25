import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .service import send_message, is_registered_user
from .serializers import SendTestWhatsAppSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def test_send_whatsapp(request):
    """
    Simple endpoint to test sending a WhatsApp message.
    
    This is a TESTING endpoint only and should not be used in production.
    
    Request body:
    {
        "phone_number": "2348012345678",
        "message_text": "Hello, this is a test message!",
        "media_url": "https://example.com/image.jpg" (optional)
    }
    
    Response:
    {
        "success": true/false,
        "message_id": "external_id_from_360messenger",
        "error": "Error message if failed",
        "is_whatsapp_user": true/false,
        "details": "Human-readable status"
    }
    """
    serializer = SendTestWhatsAppSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors,
                "details": "Validation failed"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    phone = serializer.validated_data['phone_number']
    text = serializer.validated_data['message_text']
    media_url = serializer.validated_data.get('media_url', '')
    
    # Check if phone is registered on WhatsApp
    is_registered = is_registered_user(phone)
    
    # Send the message
    result = send_message(
        phone,
        text,
        media_url=media_url if media_url else None
    )
    
    # Format response
    response_data = {
        "success": result['success'],
        "message_id": result['message_id'],
        "error": result['error'],
        "is_whatsapp_user": is_registered,
        "details": ""
    }
    
    if result['success']:
        response_data["details"] = (
            f"✅ Message sent successfully to {phone}. "
            f"Message ID: {result['message_id']}"
        )
        http_status = status.HTTP_200_OK
    else:
        response_data["details"] = (
            f"❌ Failed to send message to {phone}. "
            f"Error: {result['error']}"
        )
        http_status = status.HTTP_400_BAD_REQUEST
    
    return Response(response_data, status=http_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_whatsapp_info(request):
    """
    Get info about the WhatsApp messaging system.
    
    Returns:
    {
        "configured": true/false,
        "api_key_present": true/false,
        "endpoint": "/api/whatsapp/test-send/",
        "help": "..."
    }
    """
    from django.conf import settings
    
    api_key = getattr(settings, 'MESSENGER360_API_KEY', '')
    
    return Response({
        "configured": bool(api_key),
        "api_key_present": bool(api_key),
        "api_key_preview": f"{api_key[:10]}...{api_key[-5:]}" if api_key else "Not set",
        "endpoint": "/api/whatsapp/test-send/",
        "help": "POST to test-send/ with phone_number, message_text, and optional media_url",
        "phone_format": "International format (e.g., 2348012345678 for Nigeria)",
        "base_url": "https://api.360messenger.com/v2/"
    })
