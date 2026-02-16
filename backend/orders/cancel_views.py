"""
Order Cancellation Views

Handles order cancellation with automatic escrow refund.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone

from .models import Order
from wallet.escrow import EscrowManager


class CancelOrderView(APIView):
    """
    Cancel an order and refund escrowed funds if applicable.
    
    POST /api/orders/{order_number}/cancel/
    {
        "reason": "Customer requested cancellation"
    }
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, order_number):
        """Cancel an order and process refund if needed"""
        
        # Get cancellation reason
        reason = request.data.get('reason', 'Order canceled by merchant')
        
        # Get the order
        try:
            order = Order.objects.select_for_update().get(
                order_number=order_number,
                user=request.user
            )
        except Order.DoesNotExist:
            return Response(
                {'error': f'Order {order_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if order can be canceled
        if order.status == 'Canceled':
            return Response(
                {'error': 'Order is already canceled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order.status == 'Delivered':
            return Response(
                {'error': 'Cannot cancel a delivered order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if escrow was released (delivery completed)
        if order.escrow_held and order.escrow_released:
            return Response(
                {'error': 'Cannot cancel order - delivery already completed and funds released'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process escrow refund if applicable
        refund_processed = False
        refund_amount = 0
        
        if order.payment_method == 'wallet' and order.escrow_held and not order.escrow_released:
            try:
                # Refund the escrowed funds
                escrow_transaction, refund_transaction = EscrowManager.refund_funds(
                    order_number=order.order_number,
                    reason=reason
                )
                
                refund_processed = True
                refund_amount = float(refund_transaction.amount)
                
            except ValueError as e:
                return Response(
                    {'error': f'Failed to process refund: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update order status
        old_status = order.status
        order.status = 'Canceled'
        order.updated_at = timezone.now()
        order.save()
        
        # Prepare response
        response_data = {
            'success': True,
            'message': f'Order {order_number} has been canceled',
            'order': {
                'order_number': order.order_number,
                'old_status': old_status,
                'new_status': order.status,
                'payment_method': order.payment_method,
                'total_amount': float(order.total_amount),
                'canceled_at': order.updated_at.isoformat()
            },
            'refund': {
                'processed': refund_processed,
                'amount': refund_amount,
                'reason': reason if refund_processed else None
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class CancelableOrdersView(APIView):
    """
    Get list of orders that can be canceled.
    
    GET /api/orders/cancelable/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all cancelable orders for the current user"""
        
        # Orders that can be canceled: not Delivered and not already Canceled
        cancelable_orders = Order.objects.filter(
            user=request.user
        ).exclude(
            status__in=['Delivered', 'Canceled']
        ).order_by('-created_at')
        
        orders_data = []
        for order in cancelable_orders:
            orders_data.append({
                'order_number': order.order_number,
                'status': order.status,
                'payment_method': order.payment_method,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at.isoformat(),
                'can_refund': order.escrow_held and not order.escrow_released,
                'escrow_held': order.escrow_held,
                'escrow_released': order.escrow_released
            })
        
        return Response({
            'count': len(orders_data),
            'orders': orders_data
        }, status=status.HTTP_200_OK)

