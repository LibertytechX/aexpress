from django.urls import path
from . import views

urlpatterns = [
    # Paystack public key
    path('paystack-key/', views.get_paystack_public_key, name='paystack-public-key'),

    # Wallet balance
    path('balance/', views.get_wallet_balance, name='wallet-balance'),

    # Transaction history
    path('transactions/', views.get_transaction_history, name='transaction-history'),

    # Wallet funding
    path('fund/initialize/', views.initialize_payment, name='initialize-payment'),
    path('fund/verify/', views.verify_payment, name='verify-payment'),

    # Paystack webhook
    path('webhook/', views.paystack_webhook, name='paystack-webhook'),

    # CoreBanking (LibertyPay) virtual account
    path('virtual-account/', views.get_virtual_account, name='virtual-account'),

    # Called when merchant clicks "I have paid" on the bank transfer modal
    path('fund/transfer-claim/', views.confirm_transfer_payment, name='transfer-claim'),

    # CoreBanking webhook (receives transfer notifications)
    path('corebanking-webhook/', views.corebanking_webhook, name='corebanking-webhook'),
]

