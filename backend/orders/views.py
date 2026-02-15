from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from decimal import Decimal
from .models import Order, Delivery, Vehicle
from .serializers import (
    OrderSerializer,
    VehicleSerializer,
    QuickSendSerializer,
    MultiDropSerializer,
    BulkImportSerializer
)
from wallet.models import Wallet


class VehicleListView(APIView):
    """API endpoint to list all available vehicles."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all active vehicles with pricing."""
        vehicles = Vehicle.objects.filter(is_active=True)
        serializer = VehicleSerializer(vehicles, many=True)

        return Response({
            'success': True,
            'vehicles': serializer.data
        }, status=status.HTTP_200_OK)


class QuickSendView(APIView):
    """API endpoint for Quick Send order creation."""

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """Create a Quick Send order with single delivery."""
        serializer = QuickSendSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Get vehicle
        vehicle = Vehicle.objects.get(name=data['vehicle'], is_active=True)

        # Calculate total amount (single delivery)
        total_amount = vehicle.base_price

        # Create order
        order = Order.objects.create(
            user=request.user,
            mode='quick',
            vehicle=vehicle,
            pickup_address=data['pickup_address'],
            sender_name=data['sender_name'],
            sender_phone=data['sender_phone'],
            payment_method=data['payment_method'],
            total_amount=total_amount,
            notes=data.get('notes', ''),
            scheduled_pickup_time=data.get('scheduled_pickup_time')
        )

        # Create single delivery
        Delivery.objects.create(
            order=order,
            dropoff_address=data['dropoff_address'],
            receiver_name=data['receiver_name'],
            receiver_phone=data['receiver_phone'],
            package_type=data.get('package_type', 'Box'),
            notes=data.get('notes', ''),
            sequence=1
        )

        # Auto-debit wallet if payment method is wallet
        if data['payment_method'] == 'wallet':
            try:
                wallet = Wallet.objects.get(user=request.user)

                # Check if wallet has sufficient balance
                if not wallet.can_debit(total_amount):
                    # Delete the order and delivery (rollback)
                    order.delete()
                    return Response({
                        'success': False,
                        'errors': {'wallet': [f'Insufficient wallet balance. Required: ₦{total_amount}, Available: ₦{wallet.balance}']}
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Debit wallet
                wallet.debit(
                    amount=total_amount,
                    description=f'Payment for order #{order.order_number}',
                    reference=f'ORDER-{order.order_number}'
                )
            except Wallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = Wallet.objects.create(user=request.user)
                order.delete()
                return Response({
                    'success': False,
                    'errors': {'wallet': ['Insufficient wallet balance. Please fund your wallet first.']}
                }, status=status.HTTP_400_BAD_REQUEST)

        # Return created order
        order_serializer = OrderSerializer(order)

        return Response({
            'success': True,
            'message': 'Quick Send order created successfully!',
            'order': order_serializer.data
        }, status=status.HTTP_201_CREATED)


class MultiDropView(APIView):
    """API endpoint for Multi-Drop order creation."""

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """Create a Multi-Drop order with multiple deliveries."""
        serializer = MultiDropSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Get vehicle
        vehicle = Vehicle.objects.get(name=data['vehicle'], is_active=True)

        # Calculate total amount (number of deliveries * vehicle price)
        num_deliveries = len(data['deliveries'])
        total_amount = vehicle.base_price * num_deliveries

        # Create order
        order = Order.objects.create(
            user=request.user,
            mode='multi',
            vehicle=vehicle,
            pickup_address=data['pickup_address'],
            sender_name=data['sender_name'],
            sender_phone=data['sender_phone'],
            payment_method=data['payment_method'],
            total_amount=total_amount,
            notes=data.get('notes', ''),
            scheduled_pickup_time=data.get('scheduled_pickup_time')
        )

        # Create multiple deliveries
        for idx, delivery_data in enumerate(data['deliveries'], start=1):
            Delivery.objects.create(
                order=order,
                dropoff_address=delivery_data['dropoff_address'],
                receiver_name=delivery_data['receiver_name'],
                receiver_phone=delivery_data['receiver_phone'],
                package_type=delivery_data.get('package_type', 'Box'),
                notes=delivery_data.get('notes', ''),
                sequence=idx
            )

        # Auto-debit wallet if payment method is wallet
        if data['payment_method'] == 'wallet':
            try:
                wallet = Wallet.objects.get(user=request.user)

                # Check if wallet has sufficient balance
                if not wallet.can_debit(total_amount):
                    # Delete the order and deliveries (rollback)
                    order.delete()
                    return Response({
                        'success': False,
                        'errors': {'wallet': [f'Insufficient wallet balance. Required: ₦{total_amount}, Available: ₦{wallet.balance}']}
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Debit wallet
                wallet.debit(
                    amount=total_amount,
                    description=f'Payment for order #{order.order_number}',
                    reference=f'ORDER-{order.order_number}'
                )
            except Wallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = Wallet.objects.create(user=request.user)
                order.delete()
                return Response({
                    'success': False,
                    'errors': {'wallet': ['Insufficient wallet balance. Please fund your wallet first.']}
                }, status=status.HTTP_400_BAD_REQUEST)

        # Return created order
        order_serializer = OrderSerializer(order)

        return Response({
            'success': True,
            'message': f'Multi-Drop order created with {num_deliveries} deliveries!',
            'order': order_serializer.data
        }, status=status.HTTP_201_CREATED)


class BulkImportView(APIView):
    """API endpoint for Bulk Import order creation."""

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """Create a Bulk Import order with multiple deliveries."""
        serializer = BulkImportSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Get vehicle
        vehicle = Vehicle.objects.get(name=data['vehicle'], is_active=True)

        # Calculate total amount (number of deliveries * vehicle price)
        num_deliveries = len(data['deliveries'])
        total_amount = vehicle.base_price * num_deliveries

        # Create order
        order = Order.objects.create(
            user=request.user,
            mode='bulk',
            vehicle=vehicle,
            pickup_address=data['pickup_address'],
            sender_name=data['sender_name'],
            sender_phone=data['sender_phone'],
            payment_method=data['payment_method'],
            total_amount=total_amount,
            notes=data.get('notes', ''),
            scheduled_pickup_time=data.get('scheduled_pickup_time')
        )

        # Create multiple deliveries
        for idx, delivery_data in enumerate(data['deliveries'], start=1):
            Delivery.objects.create(
                order=order,
                dropoff_address=delivery_data['dropoff_address'],
                receiver_name=delivery_data['receiver_name'],
                receiver_phone=delivery_data['receiver_phone'],
                package_type=delivery_data.get('package_type', 'Box'),
                notes=delivery_data.get('notes', ''),
                sequence=idx
            )

        # Auto-debit wallet if payment method is wallet
        if data['payment_method'] == 'wallet':
            try:
                wallet = Wallet.objects.get(user=request.user)

                # Check if wallet has sufficient balance
                if not wallet.can_debit(total_amount):
                    # Delete the order and deliveries (rollback)
                    order.delete()
                    return Response({
                        'success': False,
                        'errors': {'wallet': [f'Insufficient wallet balance. Required: ₦{total_amount}, Available: ₦{wallet.balance}']}
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Debit wallet
                wallet.debit(
                    amount=total_amount,
                    description=f'Payment for order #{order.order_number}',
                    reference=f'ORDER-{order.order_number}'
                )
            except Wallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = Wallet.objects.create(user=request.user)
                order.delete()
                return Response({
                    'success': False,
                    'errors': {'wallet': ['Insufficient wallet balance. Please fund your wallet first.']}
                }, status=status.HTTP_400_BAD_REQUEST)

        # Return created order
        order_serializer = OrderSerializer(order)

        return Response({
            'success': True,
            'message': f'Bulk Import order created with {num_deliveries} deliveries!',
            'order': order_serializer.data
        }, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    """API endpoint to list all orders for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all orders for the current user with optional filtering."""
        # Get query parameters
        status_filter = request.query_params.get('status', None)
        mode_filter = request.query_params.get('mode', None)
        limit = request.query_params.get('limit', None)

        # Base queryset
        orders = Order.objects.filter(user=request.user).select_related('vehicle').prefetch_related('deliveries')

        # Apply filters
        if status_filter:
            orders = orders.filter(status=status_filter)

        if mode_filter:
            orders = orders.filter(mode=mode_filter)

        # Apply limit
        if limit:
            try:
                orders = orders[:int(limit)]
            except ValueError:
                pass

        # Serialize
        serializer = OrderSerializer(orders, many=True)

        return Response({
            'success': True,
            'count': len(serializer.data),
            'orders': serializer.data
        }, status=status.HTTP_200_OK)


class OrderDetailView(APIView):
    """API endpoint to get details of a specific order."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_number):
        """Get order details by order number."""
        try:
            order = Order.objects.select_related('vehicle').prefetch_related('deliveries').get(
                order_number=order_number,
                user=request.user
            )
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Order not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order)

        return Response({
            'success': True,
            'order': serializer.data
        }, status=status.HTTP_200_OK)


class OrderStatsView(APIView):
    """API endpoint to get order statistics for the dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get order statistics for the current user."""
        orders = Order.objects.filter(user=request.user)

        # Calculate stats
        total_orders = orders.count()
        pending_orders = orders.filter(status__in=['Pending', 'Assigned', 'Started']).count()
        completed_orders = orders.filter(status='Done').count()
        canceled_orders = orders.filter(status__in=['CustomerCanceled', 'RiderCanceled']).count()

        # Calculate total spent (only completed orders)
        total_spent = sum(
            float(order.total_amount)
            for order in orders.filter(status='Done')
        )

        # Average delivery cost
        avg_cost = total_spent / completed_orders if completed_orders > 0 else 0

        return Response({
            'success': True,
            'stats': {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'completed_orders': completed_orders,
                'canceled_orders': canceled_orders,
                'total_spent': round(total_spent, 2),
                'average_cost': round(avg_cost, 2)
            }
        }, status=status.HTTP_200_OK)
