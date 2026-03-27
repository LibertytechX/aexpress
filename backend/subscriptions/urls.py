from django.urls import path
from . import views

urlpatterns = [
    path("plans/", views.SubscriptionPlanListView.as_view(), name="subscription-plan-list"),
    path(
        "plans/<uuid:plan_id>/subscribe/",
        views.MerchantActivateSubscriptionView.as_view(),
        name="subscription-activate",
    ),
    path(
        "active/", views.MerchantSubscriptionListView.as_view(), name="subscription-list"
    ),
    path(
        "invoices/<uuid:invoice_id>/",
        views.SubscriptionInvoiceDetailView.as_view(),
        name="invoice-detail",
    ),
    # Postpaid
    path(
        "postpaid/plans/", views.PostpaidPlanListView.as_view(), name="postpaid-plan-list"
    ),
    path(
        "postpaid/active/",
        views.MerchantPostpaidSubscriptionView.as_view(),
        name="postpaid-active",
    ),
    path(
        "postpaid/plans/<uuid:plan_id>/activate/",
        views.MerchantActivatePostpaidPlanView.as_view(),
        name="postpaid-activate",
    ),
    path(
        "postpaid/invoices/<uuid:invoice_id>/",
        views.PostpaidInvoiceDetailView.as_view(),
        name="postpaid-invoice-detail",
    ),
]
