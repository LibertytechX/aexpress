from django.urls import path
from .views import (
    VehicleListView,
    QuickSendView,
    MultiDropView,
    BulkImportView,
    OrderListView,
    OrderDetailView,
    OrderStatsView
)
from .escrow_views import (
    ReleaseEscrowView,
    RefundEscrowView,
    EscrowStatusView,
    EscrowHistoryView
)

app_name = 'orders'

urlpatterns = [
    # Vehicle endpoints
    path('vehicles/', VehicleListView.as_view(), name='vehicle_list'),

    # Order creation endpoints
    path('quick-send/', QuickSendView.as_view(), name='quick_send'),
    path('multi-drop/', MultiDropView.as_view(), name='multi_drop'),
    path('bulk-import/', BulkImportView.as_view(), name='bulk_import'),

    # Order management endpoints
    path('', OrderListView.as_view(), name='order_list'),
    path('stats/', OrderStatsView.as_view(), name='order_stats'),
    path('<str:order_number>/', OrderDetailView.as_view(), name='order_detail'),

    # Escrow management endpoints
    path('escrow-history/', EscrowHistoryView.as_view(), name='escrow_history'),
    path('<str:order_number>/release-escrow/', ReleaseEscrowView.as_view(), name='release_escrow'),
    path('<str:order_number>/refund-escrow/', RefundEscrowView.as_view(), name='refund_escrow'),
    path('<str:order_number>/escrow-status/', EscrowStatusView.as_view(), name='escrow_status'),
]

