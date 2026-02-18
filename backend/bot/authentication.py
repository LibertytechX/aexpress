"""
Authentication classes for WhatsApp bot API.
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from authentication.models import User
from .utils import normalize_phone_number


class BotAPIKeyAuthentication(BaseAuthentication):
    """
    Authenticate bot requests via X-API-Key header.
    Also extracts merchant from X-Merchant-Phone header if provided.
    
    Sets:
        request.user = BotServiceUser (always)
        request.merchant = User object (if X-Merchant-Phone provided and valid)
    """
    
    def authenticate(self, request):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return None  # No API key provided, let other auth methods try
        
        # Validate bot API key
        if api_key != settings.BOT_API_KEY:
            raise AuthenticationFailed('Invalid bot API key')
        
        # Bot is authenticated
        bot_user = BotServiceUser()
        
        # Try to identify merchant from phone header
        merchant_phone = request.headers.get('X-Merchant-Phone')
        if merchant_phone:
            normalized_phone = normalize_phone_number(merchant_phone)
            try:
                merchant = User.objects.select_related('wallet').get(phone=normalized_phone)
                # Attach merchant to request for easy access in views
                request.merchant = merchant
            except User.DoesNotExist:
                # Merchant not found - some endpoints (like lookup, signup) don't need this
                request.merchant = None
        else:
            request.merchant = None
        
        return (bot_user, None)


class BotServiceUser:
    """
    Dummy user object representing the WhatsApp bot service.
    Not a real Django user, just a marker for authentication.
    """
    is_authenticated = True
    is_bot = True
    is_active = True
    is_staff = False
    is_superuser = False
    
    @property
    def pk(self):
        return None
    
    @property
    def id(self):
        return None
    
    def __str__(self):
        return "WhatsApp Bot Service"
    
    def __repr__(self):
        return "<BotServiceUser>"

