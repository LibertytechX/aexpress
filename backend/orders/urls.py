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
from .cancel_views import (
    CancelOrderView,
    CancelableOrdersView
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

    # Escrow management endpoints (must come before <str:order_number>/)
    path('escrow-history/', EscrowHistoryView.as_view(), name='escrow_history'),
    path('cancelable/', CancelableOrdersView.as_view(), name='cancelable_orders'),

    # Order-specific endpoints (must come before <str:order_number>/)
    path('<str:order_number>/release-escrow/', ReleaseEscrowView.as_view(), name='release_escrow'),
    path('<str:order_number>/refund-escrow/', RefundEscrowView.as_view(), name='refund_escrow'),
    path('<str:order_number>/escrow-status/', EscrowStatusView.as_view(), name='escrow_status'),
    path('<str:order_number>/cancel/', CancelOrderView.as_view(), name='cancel_order'),

    # Generic order detail (must come last to avoid matching specific endpoints)
    path('<str:order_number>/', OrderDetailView.as_view(), name='order_detail'),
]

