"""
Permission classes for WhatsApp bot API.
"""
from rest_framework.permissions import BasePermission


class IsBotService(BasePermission):
    """
    Only allow requests authenticated with valid bot API key.
    Use for endpoints that don't require merchant context (lookup, signup).
    """
    
    def has_permission(self, request, view):
        return hasattr(request.user, 'is_bot') and request.user.is_bot


class IsBotWithMerchant(BasePermission):
    """
    Require both bot API key AND valid merchant identification.
    Use for endpoints that operate on merchant-specific data.
    """
    
    def has_permission(self, request, view):
        # Check bot is authenticated
        if not (hasattr(request.user, 'is_bot') and request.user.is_bot):
            return False
        
        # Check merchant was identified and found
        if not hasattr(request, 'merchant') or request.merchant is None:
            return False
        
        return True

