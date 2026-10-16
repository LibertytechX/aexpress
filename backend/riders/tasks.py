import base64
import io
import logging
import asyncio
from celery import shared_task
from django.conf import settings
from ably import AblyRest
from .models import OrderOffer
from .serializers import OrderOfferListSerializer

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def finalize_rider_document_upload_task(self, document_id, file_data, filename):
    """
    Background task: uploads a rider KYC document to S3 and attaches the resulting
    URL to the already-created RiderDocument record. Runs after the view has
    already responded, so the caller never waits on this.
    file_data is base64-encoded file bytes — Celery tasks can't accept file-like objects.
    """
    from dispatcher.s3_utils import upload_document_to_s3
    from .models import RiderDocument

    try:
        document = RiderDocument.objects.get(pk=document_id)
    except RiderDocument.DoesNotExist:
        logger.error(
            f"finalize_rider_document_upload_task: document {document_id} not found"
        )
        return

    file_content = base64.b64decode(file_data)
    file_obj = io.BytesIO(file_content)
    file_url = upload_document_to_s3(file_obj, filename, "riders", document.doc_type)
    if not file_url:
        logger.error(
            f"finalize_rider_document_upload_task: S3 upload failed for document {document_id}"
        )
        raise RuntimeError(f"S3 upload failed for document {document_id}")

    document.file_url = file_url
    document.save(update_fields=["file_url", "updated_at"])


@shared_task
def publish_random_order_offer():
    """
    Pick a random pending OrderOffer and publish to Ably topic 'for-you'.
    Runs every minute via Celery Beat.
    """
    try:
        # Get a random pending offer
        offer = (
            OrderOffer.objects.filter(
                status="pending", rider__isnull=True, order__status="Pending"
            )
            .order_by("?")
            .first()
        )

        if not offer:
            logger.info("No pending order offers found to publish.")
            return False

        # Serialize the offer using the mobile-app format
        serializer = OrderOfferListSerializer(offer)
        payload = serializer.data

        # Publish to Ably
        api_key = getattr(settings, "ABLY_API_KEY", "")
        if not api_key:
            logger.warning(
                "publish_random_order_offer: ABLY_API_KEY not configured, skipping publish"
            )
            return False

        async def _publish():
            client = AblyRest(api_key)
            channel = client.channels.get("for-you")
            await channel.publish("new_offer", payload)

        try:
            asyncio.run(_publish())
            logger.info(
                f"Published random order offer {offer.id} (Order: {offer.order.order_number}) to 'for-you' channel."
            )
            return True
        except Exception as exc:
            logger.error(
                f"publish_random_order_offer: Ably publish failed for offer {offer.id}: {exc}"
            )
            return False

    except Exception as e:
        logger.error(f"Error in publish_random_order_offer: {str(e)}")
        return False


@shared_task
def check_pending_rider_payout_status():
    """
    Background task to verify pending Wema CoreBanking payout transactions.
    Reconciles status and automatically issues a wallet refund if payout failed/reversed.
    """
    import uuid
    from django.db import transaction
    from wallet.models import (
        RiderPayoutTransaction,
        Wallet,
        IndependentRiderPayoutWalletPool,
    )
    from wallet.integrations import WemaCoreBankingPayoutSDK

    pending_payouts = RiderPayoutTransaction.objects.filter(
        status__in=[
            RiderPayoutTransaction.Status.PENDING,
            RiderPayoutTransaction.Status.PROCESSING,
        ]
    )

    if not pending_payouts.exists():
        return "No pending payouts to verify"

    sdk = WemaCoreBankingPayoutSDK()
    processed_count = 0

    for payout in pending_payouts:
        try:
            success, resp = sdk.verify_status(payout.reference)
            if not success:
                logger.warning(
                    f"verify_status check failed or pending for ref {payout.reference}"
                )
                continue

            transfer_status = str(
                resp.get("status")
                or resp.get("transfer_status")
                or resp.get("transaction_status")
                or ""
            ).lower()

            with transaction.atomic():
                locked_payout = RiderPayoutTransaction.objects.select_for_update().get(
                    id=payout.id
                )
                if locked_payout.status not in (
                    RiderPayoutTransaction.Status.PENDING,
                    RiderPayoutTransaction.Status.PROCESSING,
                ):
                    continue

                if transfer_status in ("success", "successful", "completed"):
                    locked_payout.status = RiderPayoutTransaction.Status.SUCCESS
                    locked_payout.corebanking_response = resp
                    locked_payout.save(
                        update_fields=["status", "corebanking_response", "updated_at"]
                    )
                    processed_count += 1
                elif transfer_status in ("failed", "rejected", "reversed") and not locked_payout.refunded:
                    # 1. Refund rider wallet
                    wallet = Wallet.objects.select_for_update().get(
                        user=locked_payout.rider.user
                    )
                    refund_ref = f"REF-{uuid.uuid4().hex[:12].upper()}"
                    wallet.credit(
                        amount=locked_payout.amount,
                        description=f"Refund for failed payout {locked_payout.reference}",
                        reference=refund_ref,
                        metadata={
                            "original_reference": locked_payout.reference,
                            "reason": f"CoreBanking status: {transfer_status}",
                        },
                    )

                    # 2. Refund payout pool
                    target_pool = (
                        locked_payout.pool
                        or IndependentRiderPayoutWalletPool.get_default_pool()
                    )
                    pool_refund_ref = f"POOL-REF-{uuid.uuid4().hex[:12].upper()}"
                    target_pool.credit(
                        amount=locked_payout.amount,
                        reference=pool_refund_ref,
                        rider=locked_payout.rider,
                        payout_transaction=locked_payout,
                        description=f"Refund for failed payout {locked_payout.reference}",
                        metadata={
                            "original_reference": locked_payout.reference,
                            "reason": f"CoreBanking status: {transfer_status}",
                        },
                    )

                    locked_payout.status = RiderPayoutTransaction.Status.FAILED
                    locked_payout.refunded = True
                    locked_payout.corebanking_response = resp
                    locked_payout.save(
                        update_fields=[
                            "status",
                            "refunded",
                            "corebanking_response",
                            "updated_at",
                        ]
                    )
                    processed_count += 1
        except Exception as e:
            logger.error(
                f"Error verifying payout status for {payout.reference}: {e}"
            )

    return f"Processed {processed_count} pending payouts"
