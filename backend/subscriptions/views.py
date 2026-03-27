import datetime
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import (
    SubscriptionInvoice,
    MerchantSubscription,
    SubscriptionPlan,
    PostpaidPlan,
    MerchantPostpaidSubscription,
    PostpaidInvoice,
)
from .serializers import (
    SubscriptionInvoiceSerializer,
    MerchantSubscriptionSerializer,
    SubscriptionPlanSerializer,
    PostpaidPlanSerializer,
    MerchantPostpaidSubscriptionSerializer,
    PostpaidInvoiceSerializer,
)
from .services import refresh_invoice_virtual_account
from sparky_utils.response import service_response
from sparky_utils.exceptions import ServiceException
from sparky_utils.advice import exception_advice
from devs.models import ErrorLog
from dispatcher.permissions import IsMerchant


class MerchantSubscriptionListView(APIView):
    """
    API endpoint to list subscriptions for the authenticated merchant.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request):
        merchant = getattr(request.user, "merchant_profile", None)
        if not merchant:
            raise ServiceException(status_code=400, message="User is not a merchant.")

        subscriptions = MerchantSubscription.objects.filter(merchant=merchant)
        current_active = subscriptions.filter(status="active").first()

        serializer = MerchantSubscriptionSerializer(subscriptions, many=True)
        data = {
            "subscriptions": serializer.data,
            "current_active": (
                MerchantSubscriptionSerializer(current_active).data
                if current_active
                else None
            ),
        }
        return service_response(
            status="success",
            message="Subscriptions retrieved successfully.",
            data=data,
            status_code=200,
        )


class SubscriptionInvoiceDetailView(APIView):
    """
    API endpoint to retrieve details for a specific invoice.
    Automatically refreshes the dynamic virtual account if expired (30m TTL).
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request, invoice_id):
        try:
            invoice = SubscriptionInvoice.objects.get(
                id=invoice_id, subscription__merchant__user=request.user
            )
        except SubscriptionInvoice.DoesNotExist:
            raise ServiceException(status_code=404, message="Invoice not found.")

        if invoice.status == "pending":
            # Automatically refresh if expired or not yet generated
            from django.utils import timezone

            if (
                not invoice.payment_info
                or not invoice.virtual_account_expiry
                or timezone.now() >= invoice.virtual_account_expiry
            ):
                refresh_invoice_virtual_account(invoice)

        serializer = SubscriptionInvoiceSerializer(invoice)
        return service_response(
            status="success",
            message="Invoice retrieved successfully.",
            data=serializer.data,
            status_code=200,
        )


class SubscriptionPlanListView(APIView):
    """
    API endpoint to list all available subscription plans.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request):
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return service_response(
            status="success",
            message="Subscription plans retrieved successfully.",
            data=serializer.data,
            status_code=200,
        )


class MerchantActivateSubscriptionView(APIView):
    """
    API endpoint for a merchant to subscribe to a plan.
    """

    permission_classes = [IsMerchant]

    @exception_advice(model_object=ErrorLog)
    def post(self, request, plan_id):
        merchant = getattr(request.user, "merchant_profile", None)
        if not merchant:
            raise ServiceException(status_code=400, message="User is not a merchant.")

        # Check if they already have an active subscription
        from .services import get_active_subscription

        if get_active_subscription(merchant):
            raise ServiceException(
                status_code=400,
                message="You already have an active subscription. Please cancel it before subscribing to a new plan.",
            )

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            raise ServiceException(
                status_code=404, message="Subscription plan not found."
            )

        from .services import activate_merchant_subscription

        subscription = activate_merchant_subscription(merchant, plan)

        serializer = MerchantSubscriptionSerializer(subscription)
        return service_response(
            status="success",
            message=f"Successfully subscribed to {plan.name} plan.",
            data=serializer.data,
            status_code=201,
        )


class PostpaidPlanListView(APIView):
    """
    API endpoint to list all available postpaid plans.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request):
        plans = PostpaidPlan.objects.filter(is_active=True)
        serializer = PostpaidPlanSerializer(plans, many=True)
        return service_response(
            status="success",
            message="Postpaid plans retrieved successfully.",
            data=serializer.data,
            status_code=200,
        )


class MerchantPostpaidSubscriptionView(APIView):
    """
    API endpoint to retrieve the current postpaid subscription for the merchant.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request):
        merchant = getattr(request.user, "merchant_profile", None)
        if not merchant:
            raise ServiceException(status_code=400, message="User is not a merchant.")

        subscription = MerchantPostpaidSubscription.objects.filter(
            merchant=merchant
        ).first()
        serializer = MerchantPostpaidSubscriptionSerializer(subscription)
        return service_response(
            status="success",
            message="Postpaid subscription retrieved successfully.",
            data=serializer.data,
            status_code=200,
        )


class MerchantActivatePostpaidPlanView(APIView):
    """
    API endpoint to activate a postpaid plan.
    """

    permission_classes = [IsMerchant]

    @exception_advice(model_object=ErrorLog)
    def post(self, request, plan_id):
        merchant = getattr(request.user, "merchant_profile", None)
        if not merchant:
            raise ServiceException(status_code=400, message="User is not a merchant.")

        # Check if they already have an active postpaid plan
        if MerchantPostpaidSubscription.objects.filter(merchant=merchant).exists():
            raise ServiceException(
                status_code=400, message="You already have an active postpaid plan."
            )

        try:
            plan = PostpaidPlan.objects.get(id=plan_id, is_active=True)
        except (PostpaidPlan.DoesNotExist, ValueError):
            raise ServiceException(status_code=404, message="Postpaid plan not found.")

        # Activate plan
        now = timezone.now()
        if plan.plan_type == "weekly":
            end_date = now + datetime.timedelta(days=7)
        else:
            end_date = now + datetime.timedelta(days=30)

        subscription = MerchantPostpaidSubscription.objects.create(
            merchant=merchant,
            plan=plan,
            status="active",
            current_period_start=now,
            current_period_end=end_date,
        )

        serializer = MerchantPostpaidSubscriptionSerializer(subscription)
        return service_response(
            status="success",
            message=f"Successfully activated {plan.name} postpaid plan.",
            data=serializer.data,
            status_code=201,
        )


class PostpaidInvoiceDetailView(APIView):
    """
    API endpoint to retrieve details for a specific postpaid invoice.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice(model_object=ErrorLog)
    def get(self, request, invoice_id):
        try:
            invoice = PostpaidInvoice.objects.get(
                id=invoice_id, subscription__merchant__user=request.user
            )
        except (PostpaidInvoice.DoesNotExist, ValueError):
            raise ServiceException(status_code=404, message="Postpaid invoice not found.")

        # Refresh virtual account if needed
        from .services import refresh_postpaid_invoice_virtual_account

        if invoice.status == "pending" and not invoice.payment_info:
            refresh_postpaid_invoice_virtual_account(invoice)

        serializer = PostpaidInvoiceSerializer(invoice)
        return service_response(
            status="success",
            message="Postpaid invoice retrieved successfully.",
            data=serializer.data,
            status_code=200,
        )
