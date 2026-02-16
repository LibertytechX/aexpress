"""
Escrow Management API Endpoints

These endpoints handle escrow operations for orders:
- Release escrow when delivery is completed
- Refund escrow when order is canceled
- Check escrow status
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction

from .models import Order
from wallet.escrow import EscrowManager


class ReleaseEscrowView(APIView):
    """Release escrowed funds when delivery is completed."""

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_number):
        """
        Release escrow for a completed order.

        URL: POST /api/orders/{order_number}/release-escrow/
        """
        try:
            # Get order and verify ownership
            order = Order.objects.get(order_number=order_number, user=request.user)

            # Verify order is completed
            if order.status != 'Done':
                return Response({
                    'success': False,
                    'error': f'Cannot release escrow. Order status is "{order.status}", must be "Done"'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verify escrow is held
            if not order.escrow_held:
                return Response({
                    'success': False,
                    'error': 'No escrow held for this order'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verify escrow not already released
            if order.escrow_released:
                return Response({
                    'success': False,
                    'error': 'Escrow already released for this order'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Release escrow
            escrow_transaction = EscrowManager.release_funds(
                order_number=order.order_number,
                description=f'Escrow released for completed order #{order.order_number}'
            )

            # Mark order as escrow released
            order.escrow_released = True
            order.save()

            return Response({
                'success': True,
                'message': f'Escrow released for order #{order.order_number}',
                'amount': float(escrow_transaction.amount),
                'order_number': order.order_number
            }, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RefundEscrowView(APIView):
    """Refund escrowed funds when order is canceled."""

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_number):
        """
        Refund escrow for a canceled order.

        URL: POST /api/orders/{order_number}/refund-escrow/
        Body: {
            "reason": "Customer canceled",
            "partial_amount": 1200.00  // Optional for partial refunds
        }
        """
        try:
            # Get order and verify ownership
            order = Order.objects.get(order_number=order_number, user=request.user)

            # Verify order is canceled
            if order.status not in ['CustomerCanceled', 'RiderCanceled', 'Failed']:
                return Response({
                    'success': False,
                    'error': f'Cannot refund escrow. Order status is "{order.status}", must be canceled or failed'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verify escrow is held
            if not order.escrow_held:
                return Response({
                    'success': False,
                    'error': 'No escrow held for this order'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get refund details
            reason = request.data.get('reason', f'Refund for {order.status} order')
            partial_amount = request.data.get('partial_amount')

            # Refund escrow
            escrow_transaction, refund_transaction = EscrowManager.refund_funds(
                order_number=order.order_number,
                reason=reason,
                partial_amount=partial_amount
            )

            return Response({
                'success': True,
                'message': f'Escrow refunded for order #{order.order_number}',
                'refund_amount': float(refund_transaction.amount),
                'refund_type': 'partial' if partial_amount else 'full',
                'order_number': order.order_number
            }, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class EscrowStatusView(APIView):
    """Get escrow status for an order."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_number):
        """
        Get escrow status for an order.

        URL: GET /api/orders/{order_number}/escrow-status/
        """
        try:
            # Get order and verify ownership
            order = Order.objects.get(order_number=order_number, user=request.user)

            # Get escrow status
            escrow_status = EscrowManager.get_escrow_status(order.order_number)

            return Response({
                'success': True,
                'order_number': order.order_number,
                'order_status': order.status,
                'escrow_held': order.escrow_held,
                'escrow_released': order.escrow_released,
                'escrow_details': escrow_status
            }, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)


class EscrowHistoryView(APIView):
    """Get escrow transaction history for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Get escrow transaction history.

        URL: GET /api/orders/escrow-history/?status=completed

        Query Parameters:
            - status: Filter by status ('pending', 'completed', 'reversed')
        """
        from wallet.models import Wallet

        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Wallet not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get status filter from query params
        status_filter = request.query_params.get('status')

        # Get escrow history
        escrow_txns = EscrowManager.get_escrow_history(wallet, status_filter)

        # Format response
        history = []
        for txn in escrow_txns:
            order_number = txn.metadata.get('order_number', 'Unknown')

            # Try to get order details
            try:
                order = Order.objects.get(order_number=order_number)
                order_status = order.status
                escrow_held = order.escrow_held
                escrow_released = order.escrow_released
            except Order.DoesNotExist:
                order_status = 'Unknown'
                escrow_held = False
                escrow_released = False

            history.append({
                'transaction_id': str(txn.id),
                'order_number': order_number,
                'order_status': order_status,
                'amount': float(txn.amount),
                'escrow_status': txn.metadata.get('escrow_status', 'unknown'),
                'transaction_status': txn.status,
                'can_refund': txn.metadata.get('can_refund', False),
                'escrow_held': escrow_held,
                'escrow_released': escrow_released,
                'created_at': txn.created_at.isoformat(),
                'description': txn.description,
                'reference': txn.reference
            })

        # Get summary statistics
        total_escrowed = EscrowManager.get_total_escrowed(wallet)
        completed_escrow = EscrowManager.get_completed_escrow_transactions(wallet)
        refunded_escrow = EscrowManager.get_refunded_escrow_transactions(wallet)

        return Response({
            'success': True,
            'summary': {
                'total_currently_escrowed': float(total_escrowed),
                'total_completed_escrow': completed_escrow.count(),
                'total_refunded_escrow': refunded_escrow.count(),
                'total_completed_amount': float(sum(txn.amount for txn in completed_escrow)),
                'total_refunded_amount': float(sum(txn.amount for txn in refunded_escrow))
            },
            'history': history,
            'count': len(history)
        }, status=status.HTTP_200_OK)

