from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from django.db import transaction as db_transaction
from django.views.decorators.csrf import csrf_exempt
import requests
import hashlib
import hmac
from decimal import Decimal

from .models import Wallet, Transaction, VirtualAccount
from .serializers import (
    WalletSerializer,
    TransactionSerializer,
    FundWalletSerializer,
    VerifyPaymentSerializer,
    VirtualAccountSerializer,
)


class TransactionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
def get_paystack_public_key(request):
    """Get Paystack public key for frontend integration"""
    return Response({
        'success': True,
        'data': {
            'public_key': settings.PAYSTACK_PUBLIC_KEY
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_balance(request):
    """Get user's wallet balance"""
    try:
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = WalletSerializer(wallet)

        return Response({
            'success': True,
            'data': serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transaction_history(request):
    """Get user's transaction history with pagination"""
    try:
        wallet, created = Wallet.objects.get_or_create(user=request.user)

        # Get query parameters
        transaction_type = request.GET.get('type', None)
        transaction_status = request.GET.get('status', None)

        # Filter transactions
        transactions = wallet.transactions.all()

        if transaction_type:
            transactions = transactions.filter(type=transaction_type)

        if transaction_status:
            transactions = transactions.filter(status=transaction_status)

        # Paginate
        paginator = TransactionPagination()
        paginated_transactions = paginator.paginate_queryset(transactions, request)

        serializer = TransactionSerializer(paginated_transactions, many=True)

        return paginator.get_paginated_response({
            'success': True,
            'data': serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_payment(request):
    """Initialize Paystack payment for wallet funding"""
    try:
        serializer = FundWalletSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data['amount']

        # Get or create wallet
        wallet, created = Wallet.objects.get_or_create(user=request.user)

        # Initialize Paystack payment
        paystack_secret_key = settings.PAYSTACK_SECRET_KEY

        headers = {
            'Authorization': f'Bearer {paystack_secret_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'email': request.user.email,
            'amount': int(amount * 100),  # Convert to kobo
            'currency': 'NGN',
            'metadata': {
                'user_id': str(request.user.id),
                'wallet_id': str(wallet.id),
                'purpose': 'wallet_funding'
            }
        }

        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            json=payload,
            headers=headers
        )

        response_data = response.json()

        if response.status_code == 200 and response_data.get('status'):
            # Create pending transaction
            transaction_ref = response_data['data']['reference']

            Transaction.objects.create(
                wallet=wallet,
                type='credit',
                amount=amount,
                description='Wallet funding via Paystack',
                reference=transaction_ref,
                paystack_reference=transaction_ref,
                balance_before=wallet.balance,
                balance_after=wallet.balance,  # Balance unchanged until payment is verified
                status='pending',
                metadata={'paystack_response': response_data['data']}
            )

            return Response({
                'success': True,
                'data': {
                    'authorization_url': response_data['data']['authorization_url'],
                    'access_code': response_data['data']['access_code'],
                    'reference': transaction_ref
                }
            })
        else:
            return Response({
                'success': False,
                'errors': {'detail': response_data.get('message', 'Payment initialization failed')}
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'success': False,
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """Verify Paystack payment and credit wallet"""
    try:
        serializer = VerifyPaymentSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        reference = serializer.validated_data['reference']

        # Verify payment with Paystack
        paystack_secret_key = settings.PAYSTACK_SECRET_KEY

        headers = {
            'Authorization': f'Bearer {paystack_secret_key}',
        }

        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers
        )

        response_data = response.json()

        if response.status_code == 200 and response_data.get('status'):
            payment_data = response_data['data']

            # Check if payment was successful
            if payment_data['status'] == 'success':
                # Get transaction
                try:
                    transaction = Transaction.objects.get(paystack_reference=reference)

                    # Check if already processed
                    if transaction.status == 'completed':
                        return Response({
                            'success': True,
                            'data': {
                                'message': 'Payment already processed',
                                'transaction': TransactionSerializer(transaction).data
                            }
                        })

                    # Credit wallet
                    with db_transaction.atomic():
                        wallet = transaction.wallet
                        wallet.balance += transaction.amount
                        wallet.save()

                        # Update transaction
                        transaction.status = 'completed'
                        transaction.paystack_status = payment_data['status']
                        transaction.balance_after = wallet.balance
                        transaction.metadata = {
                            **transaction.metadata,
                            'paystack_verification': payment_data
                        }
                        transaction.save()

                    return Response({
                        'success': True,
                        'data': {
                            'message': 'Wallet funded successfully',
                            'transaction': TransactionSerializer(transaction).data,
                            'wallet': WalletSerializer(wallet).data
                        }
                    })

                except Transaction.DoesNotExist:
                    return Response({
                        'success': False,
                        'errors': {'detail': 'Transaction not found'}
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'success': False,
                    'errors': {'detail': f'Payment {payment_data["status"]}'}
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'success': False,
                'errors': {'detail': 'Payment verification failed'}
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'success': False,
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_virtual_account(request):
    """Get or create a CoreBanking virtual account for the authenticated user."""
    try:
        try:
            virtual_account = VirtualAccount.objects.get(user=request.user)
        except VirtualAccount.DoesNotExist:
            from .corebanking_service import create_virtual_account
            virtual_account = create_virtual_account(request.user)

        serializer = VirtualAccountSerializer(virtual_account)
        return Response({
            'success': True,
            'data': serializer.data,
        })

    except Exception as e:
        return Response({
            'success': False,
            'errors': {'detail': str(e)},
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])
@csrf_exempt
def corebanking_webhook(request):
    """
    Handle CoreBanking (LibertyPay) webhook for incoming transfer notifications.
    Credits the merchant's wallet when a CREDIT settlement is received.
    """
    try:
        # Optional signature verification
        webhook_secret = settings.COREBANKING_WEBHOOK_SECRET
        if webhook_secret:
            signature = request.headers.get('X-Webhook-Signature', '')
            expected = hmac.new(
                webhook_secret.encode('utf-8'),
                request.body,
                hashlib.sha256,
            ).hexdigest()
            if signature != expected:
                return Response({
                    'success': False,
                    'errors': {'detail': 'Invalid signature'},
                }, status=status.HTTP_400_BAD_REQUEST)

        data = request.data

        # Only process settled credit transactions
        if data.get('transaction_type') != 'CREDIT' or not data.get('settlement_status'):
            return Response({'success': True})

        recipient_account_number = data.get('recipient_account_number', '').strip()
        amount = data.get('amount', 0)
        transaction_reference = data.get('transaction_reference', '').strip()
        payer_name = data.get('payer_account_name', 'Bank Transfer')

        if not recipient_account_number or not transaction_reference:
            return Response({
                'success': False,
                'errors': {'detail': 'Missing required fields'},
            }, status=status.HTTP_400_BAD_REQUEST)

        # Idempotency: skip if already processed
        if Transaction.objects.filter(reference=transaction_reference).exists():
            return Response({'success': True})

        # Find the merchant via virtual account
        try:
            virtual_account = VirtualAccount.objects.select_related('user').get(
                account_number=recipient_account_number
            )
        except VirtualAccount.DoesNotExist:
            return Response({
                'success': False,
                'errors': {'detail': 'Virtual account not found'},
            }, status=status.HTTP_404_NOT_FOUND)

        wallet, _ = Wallet.objects.get_or_create(user=virtual_account.user)

        with db_transaction.atomic():
            wallet.credit(
                amount=Decimal(str(amount)),
                description=f'Bank transfer from {payer_name}',
                reference=transaction_reference,
            )

        return Response({'success': True})

    except Exception as e:
        return Response({
            'success': False,
            'errors': {'detail': str(e)},
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
def paystack_webhook(request):
    """Handle Paystack webhook for payment notifications"""
    try:
        # Verify webhook signature
        paystack_secret_key = settings.PAYSTACK_SECRET_KEY
        signature = request.headers.get('X-Paystack-Signature', '')

        # Compute hash
        hash_value = hmac.new(
            paystack_secret_key.encode('utf-8'),
            request.body,
            hashlib.sha512
        ).hexdigest()

        if signature != hash_value:
            return Response({
                'success': False,
                'errors': {'detail': 'Invalid signature'}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Process webhook event
        event = request.data.get('event')
        data = request.data.get('data', {})

        if event == 'charge.success':
            reference = data.get('reference')

            try:
                transaction = Transaction.objects.get(paystack_reference=reference)

                # Check if already processed
                if transaction.status != 'completed':
                    # Credit wallet
                    with db_transaction.atomic():
                        wallet = transaction.wallet
                        wallet.balance += transaction.amount
                        wallet.save()

                        # Update transaction
                        transaction.status = 'completed'
                        transaction.paystack_status = data.get('status')
                        transaction.balance_after = wallet.balance
                        transaction.metadata = {
                            **transaction.metadata,
                            'webhook_data': data
                        }
                        transaction.save()

                return Response({'success': True})

            except Transaction.DoesNotExist:
                return Response({'success': False, 'errors': {'detail': 'Transaction not found'}})

        return Response({'success': True})

    except Exception as e:
        return Response({
            'success': False,
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
