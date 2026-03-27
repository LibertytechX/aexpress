from django.urls import path
from . import views

urlpatterns = [
    path("plans/", views.SubscriptionPlanListView.as_view(), name="subscription-plan-list"),
    path("plans/<uuid:plan_id>/subscribe/", views.MerchantActivateSubscriptionView.as_view(), name="subscription-activate"),
    path("active/", views.MerchantSubscriptionListView.as_view(), name="subscription-list"),
    path("invoices/<uuid:invoice_id>/", views.SubscriptionInvoiceDetailView.as_view(), name="invoice-detail"),
]
