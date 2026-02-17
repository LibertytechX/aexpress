from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import User, Address
from .serializers import (
    UserSerializer,
    SignupSerializer,
    LoginSerializer,
    UserProfileSerializer,
    AddressSerializer
)


class SignupView(APIView):
    """API endpoint for user registration."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Register a new merchant user."""
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'success': True,
                'message': 'Account created successfully!',
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """API endpoint for user login."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Authenticate user and return JWT tokens."""
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'success': True,
                'message': 'Login successful!',
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """API endpoint for getting and updating user profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get current user profile."""
        serializer = UserSerializer(request.user)
        return Response({
            'success': True,
            'user': serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request):
        """Update current user profile."""
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully!',
                'user': UserSerializer(request.user).data
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """API endpoint for user logout."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Logout user by blacklisting the refresh token."""
        try:
            refresh_token = request.data.get('refresh_token')

            if not refresh_token:
                return Response({
                    'success': False,
                    'message': 'Refresh token is required.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                'success': True,
                'message': 'Logout successful!'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': 'Invalid token or token already blacklisted.'
            }, status=status.HTTP_400_BAD_REQUEST)


class AddressListCreateView(APIView):
    """API endpoint for listing and creating addresses."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all addresses for current user."""
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response({
            'success': True,
            'addresses': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new address."""
        serializer = AddressSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Address added successfully!',
                'address': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AddressDetailView(APIView):
    """API endpoint for updating and deleting a specific address."""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, address_id):
        """Get address object ensuring it belongs to current user."""
        return get_object_or_404(Address, id=address_id, user=request.user)

    def put(self, request, address_id):
        """Update an address."""
        address = self.get_object(request, address_id)
        serializer = AddressSerializer(address, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Address updated successfully!',
                'address': serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, address_id):
        """Delete an address."""
        address = self.get_object(request, address_id)
        address.delete()

        return Response({
            'success': True,
            'message': 'Address deleted successfully!'
        }, status=status.HTTP_200_OK)


class SetDefaultAddressView(APIView):
    """API endpoint for setting an address as default."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, address_id):
        """Set an address as default."""
        address = get_object_or_404(Address, id=address_id, user=request.user)

        # Unset other defaults
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

        # Set this as default
        address.is_default = True
        address.save()

        return Response({
            'success': True,
            'message': 'Default address updated!',
            'address': AddressSerializer(address).data
        }, status=status.HTTP_200_OK)
