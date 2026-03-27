from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import SubscriptionInvoice, MerchantSubscription
from .serializers import SubscriptionInvoiceSerializer, MerchantSubscriptionSerializer
from .services import refresh_invoice_virtual_account
from sparky_utils.response import service_response
from sparky_utils.exceptions import ServiceException, exception_advice


class MerchantSubscriptionListView(APIView):
    """
    API endpoint to list subscriptions for the authenticated merchant.
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice()
    def get(self, request):
        merchant = getattr(request.user, "merchant_profile", None)
        if not merchant:
            raise ServiceException(status_code=400, message="User is not a merchant.")

        subscriptions = MerchantSubscription.objects.filter(merchant=merchant)
        serializer = MerchantSubscriptionSerializer(subscriptions, many=True)
        return service_response(
            status="success",
            message="Subscriptions retrieved successfully.",
            data=serializer.data,
            status_code=200,
        )


class SubscriptionInvoiceDetailView(APIView):
    """
    API endpoint to retrieve details for a specific invoice.
    Automatically refreshes the dynamic virtual account if expired (30m TTL).
    """

    permission_classes = [permissions.IsAuthenticated]

    @exception_advice()
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
