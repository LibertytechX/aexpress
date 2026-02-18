"""
Views for WhatsApp bot API endpoints.
All endpoints use API key authentication only.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta

from authentication.models import User
from wallet.models import Wallet, Transaction, VirtualAccount
from orders.models import Order, Delivery, Vehicle
from .authentication import BotAPIKeyAuthentication
from .permissions import IsBotService, IsBotWithMerchant
from .serializers import (
    BotMerchantProfileSerializer,
    BotQuickSignupSerializer,
    BotOrderSerializer,
    BotTransactionSerializer,
    BotPriceQuoteSerializer,
    BotCreateOrderSerializer,
    BotVehicleSerializer
)
from .utils import (
    normalize_phone_number,
    format_currency,
    format_currency_short,
    format_order_summary
)


class MerchantLookupView(APIView):
    """
    GET /api/bot/lookup/?phone=2348012345678

    Lookup merchant by phone number.
    Returns merchant profile if found.
    """
    authentication_classes = [BotAPIKeyAuthentication]
    permission_classes = [IsBotService]

    def get(self, request):
        phone = request.query_params.get('phone')

        if not phone:
            return Response({
                'success': False,
                'message': 'Phone number is required',
                'bot_response': "I need your phone number to look you up."
            }, status=status.HTTP_400_BAD_REQUEST)

        normalized_phone = normalize_phone_number(phone)

        try:
            user = User.objects.select_related('wallet').get(phone=normalized_phone)

            serializer = BotMerchantProfileSerializer(user)

            # Get quick stats
            active_orders = Order.objects.filter(
                user=user,
                status__in=['pending', 'assigned', 'picked_up', 'in_transit']
            ).count()

            wallet_balance = user.wallet.balance

            return Response({
                'success': True,
                'data': serializer.data,
                'stats': {
                    'active_orders': active_orders,
                    'wallet_balance': wallet_balance
                },
                'bot_response': f"Hey {user.contact_name}! You've got {format_currency(wallet_balance)} in your wallet and {active_orders} active order{'s' if active_orders != 1 else ''}."
            })

        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Merchant not found',
                'bot_response': "I don't have this number on file yet. Want to sign up? Just tell me your business name."
            }, status=status.HTTP_404_NOT_FOUND)


class QuickSignupView(APIView):
    """
    POST /api/bot/signup/

    Passwordless merchant signup for WhatsApp bot.
    Creates merchant account with phone verification via WhatsApp.
    """
    authentication_classes = [BotAPIKeyAuthentication]
    permission_classes = [IsBotService]

    def post(self, request):
        serializer = BotQuickSignupSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
                'bot_response': "I need your phone number, business name, and your name to get you set up."
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        normalized_phone = normalize_phone_number(data['phone'])

        # Check if merchant already exists
        if User.objects.filter(phone=normalized_phone).exists():
            return Response({
                'success': False,
                'message': 'Merchant already exists with this phone number',
                'bot_response': "You're already signed up! Let me look up your account..."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create merchant (passwordless - WhatsApp is the auth)
        import secrets
        random_password = secrets.token_urlsafe(32)

        # Generate placeholder email (bot users don't need real email)
        placeholder_email = f"whatsapp_{normalized_phone}@axpress.bot"

        user = User.objects.create_user(
            phone=normalized_phone,
            email=placeholder_email,
            business_name=data['business_name'],
            contact_name=data['contact_name'],
            address=data.get('business_address', ''),
            password=random_password,  # Random password, never shared
            phone_verified=True,  # WhatsApp verified
        )

        # Wallet is auto-created via signal

        profile_serializer = BotMerchantProfileSerializer(user)

        return Response({
            'success': True,
            'data': profile_serializer.data,
            'bot_response': f"Sharp, {user.contact_name} from {user.business_name} — you're in ✅\nYour wallet starts at ₦0. Ready to create your first delivery?"
        }, status=status.HTTP_201_CREATED)


class DashboardSummaryView(APIView):
    """
    GET /api/bot/summary/

    Dashboard summary: wallet balance + active orders + today's stats.
    Requires merchant identification via X-Merchant-Phone header.
    """
    authentication_classes = [BotAPIKeyAuthentication]
    permission_classes = [IsBotWithMerchant]

    def get(self, request):
        merchant = request.merchant
        wallet = merchant.wallet

        # Get active orders
        active_orders = Order.objects.filter(
            user=merchant,
            status__in=['pending', 'assigned', 'picked_up', 'in_transit']
        )
        active_count = active_orders.count()

        # Get today's stats
        today = timezone.now().date()

        completed_today = Order.objects.filter(
            user=merchant,
            status='delivered',
            created_at__date=today
        ).count()

        spent_today = Transaction.objects.filter(
            wallet=wallet,
            type='debit',
            created_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Recent orders
        recent_orders = Order.objects.filter(user=merchant).order_by('-created_at')[:5]

        # Last transaction
        last_transaction = Transaction.objects.filter(wallet=wallet).order_by('-created_at').first()

        return Response({
            'success': True,
            'data': {
                'wallet_balance': wallet.balance,
                'active_orders_count': active_count,
                'completed_today': completed_today,
                'spent_today': spent_today,
                'recent_orders': BotOrderSerializer(recent_orders, many=True).data,
                'last_transaction': BotTransactionSerializer(last_transaction).data if last_transaction else None
            },
            'bot_response': f"You've got {format_currency(wallet.balance)} in your wallet and {active_count} active order{'s' if active_count != 1 else ''}."
        })


class GetPriceQuoteView(APIView):
    """
    POST /api/bot/orders/get-price/

    Calculate delivery price from pickup/dropoff addresses.
    Requires merchant identification.
    """
    authentication_classes = [BotAPIKeyAuthentication]
    permission_classes = [IsBotWithMerchant]

    def post(self, request):
        serializer = BotPriceQuoteSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
                'bot_response': "I need both pickup and dropoff addresses to calculate the price."
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        pickup_address = data['pickup_address']
        dropoff_address = data['dropoff_address']
        vehicle_type = data.get('vehicle_type', '').lower()

        # Import geocoding utility from orders app
        from orders.utils import geocode_address, calculate_route

        # Geocode addresses
        pickup_coords = geocode_address(pickup_address)
        dropoff_coords = geocode_address(dropoff_address)

        if not pickup_coords or not dropoff_coords:
            return Response({
                'success': False,
                'message': 'Could not geocode addresses',
                'bot_response': "I couldn't find those addresses. Can you be more specific?"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calculate route
        route_data = calculate_route(pickup_coords, [dropoff_coords])

        if not route_data:
            return Response({
                'success': False,
                'message': 'Could not calculate route',
                'bot_response': "I couldn't calculate the route. Try different addresses?"
            }, status=status.HTTP_400_BAD_REQUEST)

        distance_km = route_data['distance_km']
        duration_minutes = route_data['duration_minutes']

        # Get vehicle pricing
        if vehicle_type:
            vehicles = Vehicle.objects.filter(name__iexact=vehicle_type, is_active=True)
        else:
            vehicles = Vehicle.objects.filter(is_active=True).order_by('base_price')

        prices = []
        for vehicle in vehicles:
            price = vehicle.calculate_fare(distance_km, duration_minutes)
            prices.append({
                'vehicle': vehicle.name,
                'price': price,
                'formatted_price': format_currency(price),
                'distance_km': round(distance_km, 1),
                'duration_minutes': round(duration_minutes)
            })

        # Build bot response
        if len(prices) == 1:
            bot_msg = f"{prices[0]['vehicle'].title()}: {prices[0]['formatted_price']} ({prices[0]['distance_km']}km, ~{prices[0]['duration_minutes']} mins)"
        else:
            price_lines = [f"{p['vehicle'].title()}: {p['formatted_price']}" for p in prices]
            bot_msg = f"Here are your options:\n" + "\n".join(price_lines) + f"\n\n({prices[0]['distance_km']}km, ~{prices[0]['duration_minutes']} mins)"

        return Response({
            'success': True,
            'data': {
                'prices': prices,
                'distance_km': distance_km,
                'duration_minutes': duration_minutes
            },
            'bot_response': bot_msg
        })


class CreateOrderView(APIView):
    """
    POST /api/bot/orders/create/

    Create order via bot (bot-friendly version of quick-send).
    Requires merchant identification.
    """
    authentication_classes = [BotAPIKeyAuthentication]
    permission_classes = [IsBotWithMerchant]

    def post(self, request):
        serializer = BotCreateOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
                'bot_response': "I need all the delivery details to create the order."
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        merchant = request.merchant

        # Get vehicle
        try:
            vehicle = Vehicle.objects.get(name__iexact=data['vehicle_type'], is_active=True)
        except Vehicle.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid vehicle type',
                'bot_response': "That vehicle type isn't available. Choose bike, car, or van."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Import geocoding from orders app
        from orders.utils import geocode_address, calculate_route

        # Geocode addresses
        pickup_coords = geocode_address(data['pickup_address'])
        dropoff_coords = geocode_address(data['dropoff_address'])

        if not pickup_coords or not dropoff_coords:
            return Response({
                'success': False,
                'message': 'Could not geocode addresses',
                'bot_response': "I couldn't find those addresses. Can you be more specific?"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calculate route and price
        route_data = calculate_route(pickup_coords, [dropoff_coords])

        if not route_data:
            return Response({
                'success': False,
                'message': 'Could not calculate route',
                'bot_response': "I couldn't calculate the route. Try different addresses?"
            }, status=status.HTTP_400_BAD_REQUEST)

        distance_km = route_data['distance_km']
        duration_minutes = route_data['duration_minutes']
        total_amount = vehicle.calculate_fare(distance_km, duration_minutes)

        # Check wallet balance
        if merchant.wallet.balance < total_amount:
            return Response({
                'success': False,
                'message': 'Insufficient wallet balance',
                'bot_response': f"You need {format_currency(total_amount)} but only have {format_currency(merchant.wallet.balance)}. Top up your wallet first."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create order
        from django.db import transaction as db_transaction

        with db_transaction.atomic():
            order = Order.objects.create(
                user=merchant,
                vehicle=vehicle,
                mode='quick_send',
                pickup_address=data['pickup_address'],
                sender_name=data['pickup_contact_name'],
                sender_phone=data['pickup_contact_phone'],
                total_amount=total_amount,
                distance_km=distance_km,
                duration_minutes=duration_minutes,
                status='pending'
            )

            # Create delivery
            Delivery.objects.create(
                order=order,
                dropoff_address=data['dropoff_address'],
                receiver_name=data['dropoff_contact_name'],
                receiver_phone=data['dropoff_contact_phone'],
                package_type=data.get('package_type', 'parcel'),
                notes=data.get('dropoff_notes', '')
            )

            # Deduct from wallet (escrow)
            merchant.wallet.debit(
                amount=total_amount,
                description=f"Order {order.order_number}",
                reference=f"order_{order.order_number}"
            )

        order_serializer = BotOrderSerializer(order)

        return Response({
            'success': True,
            'data': order_serializer.data,
            'bot_response': f"Order created! {order.order_number} — {format_currency(total_amount)}\nWe'll notify you when a rider picks it up."
        }, status=status.HTTP_201_CREATED)


class ListOrdersView(APIView):
    """
    GET /api/bot/orders/

    List merchant's orders with optional status filter.
    Requires merchant identification.
    """
    authentication_classes = [BotAPIKeyAuthentication]
    permission_classes = [IsBotWithMerchant]

    def get(self, request):
        merchant = request.merchant
        status_filter = request.query_params.get('status', '').lower()

        orders = Order.objects.filter(user=merchant).order_by('-created_at')

        if status_filter:
            orders = orders.filter(status=status_filter)

        # Limit to recent 20
        orders = orders[:20]

        serializer = BotOrderSerializer(orders, many=True)

        count = orders.count()
        bot_msg = f"You have {count} order{'s' if count != 1 else ''}."

        return Response({
            'success': True,
            'data': serializer.data,
            'bot_response': bot_msg
        })


class OrderDetailView(APIView):
    """
    GET /api/bot/orders/<order_number>/

    Get order details and tracking info.
    Requires merchant identification.
    """
    authentication_classes = [BotAPIKeyAuthentication]
    permission_classes = [IsBotWithMerchant]

    def get(self, request, order_number):
        merchant = request.merchant

        try:
            order = Order.objects.select_related('vehicle').prefetch_related('deliveries').get(
                order_number=order_number,
                user=merchant
            )
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Order not found',
                'bot_response': "I couldn't find that order."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = BotOrderSerializer(order)

        return Response({
            'success': True,
            'data': serializer.data,
            'bot_response': format_order_summary(order)
        })


class CancelOrderView(APIView):
    """
    POST /api/bot/orders/<order_number>/cancel/

    Cancel order and refund to wallet.
    Requires merchant identification.
    """
    authentication_classes = [BotAPIKeyAuthentication]
    permission_classes = [IsBotWithMerchant]

    def post(self, request, order_number):
        merchant = request.merchant

        try:
            order = Order.objects.get(order_number=order_number, user=merchant)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Order not found',
                'bot_response': "I couldn't find that order."
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if order can be cancelled
        if order.status in ['delivered', 'cancelled']:
            return Response({
                'success': False,
                'message': f'Cannot cancel {order.status} order',
                'bot_response': f"This order is already {order.status}. Can't cancel it."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cancel and refund
        from django.db import transaction as db_transaction

        with db_transaction.atomic():
            order.status = 'cancelled'
            order.save()

            # Refund to wallet
            merchant.wallet.credit(
                amount=order.total_amount,
                description=f"Refund for cancelled order {order.order_number}",
                reference=f"refund_{order.order_number}"
            )

        return Response({
            'success': True,
            'data': {
                'order_number': order.order_number,
                'refund_amount': order.total_amount,
                'new_balance': merchant.wallet.balance
            },
            'bot_response': f"Order {order.order_number} cancelled. {format_currency(order.total_amount)} refunded to your wallet."
        })


class WalletBalanceView(APIView):
    """
    GET /api/bot/wallet/balance/

    Get wallet balance.
    Requires merchant identification.
    """
    authentication_classes = [BotAPIKeyAuthentication]
    permission_classes = [IsBotWithMerchant]

    def get(self, request):
        merchant = request.merchant
        balance = merchant.wallet.balance

        return Response({
            'success': True,
            'data': {
                'balance': balance,
                'formatted_balance': format_currency(balance)
            },
            'bot_response': f"Your wallet balance is {format_currency(balance)}."
        })


class TransactionHistoryView(APIView):
    """
    GET /api/bot/wallet/transactions/

    Get transaction history with optional filters.
    Requires merchant identification.
    """
    authentication_classes = [BotAPIKeyAuthentication]
    permission_classes = [IsBotWithMerchant]

    def get(self, request):
        merchant = request.merchant
        transaction_type = request.query_params.get('type', '').lower()

        transactions = Transaction.objects.filter(wallet=merchant.wallet).order_by('-created_at')

        if transaction_type in ['credit', 'debit']:
            transactions = transactions.filter(type=transaction_type)

        # Limit to recent 20
        transactions = transactions[:20]

        serializer = BotTransactionSerializer(transactions, many=True)

        count = transactions.count()
        bot_msg = f"You have {count} recent transaction{'s' if count != 1 else ''}."

        return Response({
            'success': True,
            'data': serializer.data,
            'bot_response': bot_msg
        })

class GetVirtualAccountView(APIView):
    """Get or create a virtual account for the merchant."""
    authentication_classes = [BotAPIKeyAuthentication]
    permission_classes = [IsBotWithMerchant]

    def get(self, request):
        merchant = request.merchant

        try:
            # Try to get existing virtual account
            try:
                virtual_account = VirtualAccount.objects.get(user=merchant)
            except VirtualAccount.DoesNotExist:
                # Create new virtual account via CoreBanking
                from wallet.corebanking_service import create_virtual_account
                virtual_account = create_virtual_account(merchant)

            # Format bot response
            bot_msg = (
                f"Your Wema Bank account:\n"
                f"{virtual_account.account_number}\n"
                f"{virtual_account.account_name}\n\n"
                f"Transfer money to this account to fund your wallet."
            )

            return Response({
                'success': True,
                'data': {
                    'account_number': virtual_account.account_number,
                    'account_name': virtual_account.account_name,
                    'bank_name': virtual_account.bank_name,
                    'bank_code': virtual_account.bank_code,
                    'is_active': virtual_account.is_active,
                },
                'bot_response': bot_msg
            })

        except Exception as e:
            return Response({
                'success': False,
                'message': str(e),
                'bot_response': 'Sorry, we couldn\'t get your account details right now. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


