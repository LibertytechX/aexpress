from django.urls import path
from . import views

urlpatterns = [
    path("active/", views.MerchantSubscriptionListView.as_view(), name="subscription-list"),
    path("invoices/<uuid:invoice_id>/", views.SubscriptionInvoiceDetailView.as_view(), name="invoice-detail"),
]
