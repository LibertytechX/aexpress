"""
URL configuration for WhatsApp bot API.
"""
from django.urls import path
from . import views

app_name = 'bot'

urlpatterns = [
    # Merchant management (bot API key only, no merchant context needed)
    path('lookup/', views.MerchantLookupView.as_view(), name='merchant_lookup'),
    path('signup/', views.QuickSignupView.as_view(), name='quick_signup'),

    # Dashboard (requires merchant context)
    path('summary/', views.DashboardSummaryView.as_view(), name='dashboard_summary'),

    # Order operations (requires merchant context)
    path('orders/get-price/', views.GetPriceQuoteView.as_view(), name='get_price'),
    path('orders/create/', views.CreateOrderView.as_view(), name='create_order'),
    path('orders/', views.ListOrdersView.as_view(), name='list_orders'),
    path('orders/<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<str:order_number>/cancel/', views.CancelOrderView.as_view(), name='cancel_order'),

    # Wallet operations (requires merchant context)
    path('wallet/balance/', views.WalletBalanceView.as_view(), name='wallet_balance'),
    path('wallet/transactions/', views.TransactionHistoryView.as_view(), name='transactions'),
    path('wallet/virtual-account/', views.GetVirtualAccountView.as_view(), name='virtual_account'),
]

