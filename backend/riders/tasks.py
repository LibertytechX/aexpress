import base64
import io
import logging
import asyncio
from datetime import timedelta
from celery import shared_task
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
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

    processed_count = 0

    for payout in pending_payouts:
        try:
            payout_mode = getattr(payout, "mode", None) or ("SANDBOX" if getattr(payout, "is_sandbox", False) else "LIVE")
            sdk = WemaCoreBankingPayoutSDK(mode=payout_mode)
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


def _publish_to_ably_channel(channel_name: str, event: str, payload: dict):
    """Publish a message to an Ably channel using the REST client."""
    api_key = getattr(settings, "ABLY_API_KEY", "")
    if not api_key:
        logger.warning(
            "publish_to_ably: ABLY_API_KEY not configured, skipping publish to %s",
            channel_name,
        )
        return

    async def _publish():
        from ably import AblyRest

        client = AblyRest(api_key)
        channel = client.channels.get(channel_name)
        await channel.publish(event, payload)
        await client.close()

    try:
        asyncio.run(_publish())
        logger.info("Published [%s] to channel %s", event, channel_name)
    except Exception as exc:
        logger.error(
            "Ably publish failed for channel %s (%s): %s", channel_name, event, exc
        )


@shared_task
def process_rider_facematch_task(
    rider_id: str, selfie_url: str, channel_name: str, log_id: str = None
):
    """
    Background Celery task for comparing independent rider selfie snapshot against their profile photo document.
    Downloads both images, invokes 3rd-party KYC CompareFacesView endpoint, processes the outcome,
    updates rider authorization/session status on failure, records audit log, and notifies via Ably.
    """
    import io
    import requests
    from dispatcher.models import Rider
    from .models import RiderDocument, RiderFaceMatchLog, RiderSession

    facematch_log = None
    if log_id:
        facematch_log = RiderFaceMatchLog.objects.filter(id=log_id).first()

    try:
        rider = Rider.objects.get(id=rider_id)
    except Rider.DoesNotExist:
        logger.error("process_rider_facematch_task: Rider %s not found", rider_id)
        if facematch_log:
            facematch_log.status = RiderFaceMatchLog.Status.ERROR
            facematch_log.error_message = f"Rider {rider_id} not found."
            facematch_log.save(update_fields=["status", "error_message", "updated_at"])
        return

    # Find reference profile photo URL
    ref_doc = (
        RiderDocument.objects.filter(
            rider=rider, doc_type=RiderDocument.DocType.PROFILE_PHOTO
        )
        .order_by("-created_at")
        .first()
    )
    ref_photo_url = (
        ref_doc.file_url if ref_doc and ref_doc.file_url else (rider.avatar or "")
    )

    if not ref_photo_url:
        err_msg = "No reference profile photo found for rider."
        logger.error("process_rider_facematch_task: %s (rider_id=%s)", err_msg, rider_id)
        if facematch_log:
            facematch_log.status = RiderFaceMatchLog.Status.ERROR
            facematch_log.error_message = err_msg
            facematch_log.save(update_fields=["status", "error_message", "updated_at"])
        _publish_to_ably_channel(
            channel_name,
            "facematch_result",
            {
                "status": "error",
                "matched": False,
                "message": err_msg,
            },
        )
        return

    # 1. Download selfie and reference photos
    try:
        selfie_resp = requests.get(selfie_url, timeout=20)
        selfie_resp.raise_for_status()
        selfie_bytes = selfie_resp.content

        ref_resp = requests.get(ref_photo_url, timeout=20)
        ref_resp.raise_for_status()
        ref_bytes = ref_resp.content
    except Exception as exc:
        err_msg = f"Failed to download face images: {str(exc)}"
        logger.error("process_rider_facematch_task: %s", err_msg)
        if facematch_log:
            facematch_log.status = RiderFaceMatchLog.Status.ERROR
            facematch_log.error_message = err_msg
            facematch_log.save(update_fields=["status", "error_message", "updated_at"])
        _publish_to_ably_channel(
            channel_name,
            "facematch_result",
            {
                "status": "error",
                "matched": False,
                "message": err_msg,
            },
        )
        return

    # 2. Call KYC service CompareFacesView endpoint
    kyc_url = getattr(
        settings,
        "KYC_SERVICE_URL",
        "http://localhost:8000/api/v1/kyc/face-match",
    )
    kyc_token = getattr(settings, "KYC_SERVICE_TOKEN", "")
    headers = {}
    if kyc_token:
        headers["Authorization"] = f"Bearer {kyc_token}"

    files = {
        "face_one": ("selfie.jpg", io.BytesIO(selfie_bytes), "image/jpeg"),
        "face_two": ("reference.jpg", io.BytesIO(ref_bytes), "image/jpeg"),
    }
    form_data = {
        "client_reference": f"rider_{rider.rider_id or rider.id}",
    }

    try:
        kyc_resp = requests.post(
            kyc_url,
            files=files,
            data=form_data,
            headers=headers,
            timeout=30,
        )
    except Exception as exc:
        err_msg = f"KYC service connection failed: {str(exc)}"
        logger.error("process_rider_facematch_task: %s", err_msg)
        if facematch_log:
            facematch_log.status = RiderFaceMatchLog.Status.ERROR
            facematch_log.error_message = err_msg
            facematch_log.save(update_fields=["status", "error_message", "updated_at"])
        _publish_to_ably_channel(
            channel_name,
            "facematch_result",
            {
                "status": "error",
                "matched": False,
                "message": err_msg,
            },
        )
        return

    # 3. Parse KYC response
    raw_response = {}
    is_match = False
    similarity = 0.0
    error_message = ""

    try:
        raw_response = kyc_resp.json()
    except Exception:
        raw_response = {"raw_text": kyc_resp.text}

    if kyc_resp.status_code == 200 and isinstance(raw_response, dict):
        data_block = raw_response.get("data", {})
        inner_data = (
            data_block.get("data", {}) if isinstance(data_block, dict) else {}
        )
        is_match = bool(inner_data.get("result", False))
        try:
            similarity = float(inner_data.get("similarity", 0.0) or 0.0)
        except (ValueError, TypeError):
            similarity = 0.0
    else:
        error_message = (
            raw_response.get("error")
            or raw_response.get("message")
            or f"KYC returned status {kyc_resp.status_code}"
        )
        is_match = False

    # 4. Handle Match Outcome
    if is_match:
        logger.info(
            "Face match SUCCESS for rider %s (similarity=%.2f)",
            rider.rider_id,
            similarity,
        )
        rider.face_verification_required = False
        rider.is_authorized = True
        rider.last_face_verified_at = timezone.now()
        rider.save(
            update_fields=[
                "face_verification_required",
                "is_authorized",
                "last_face_verified_at",
            ]
        )

        if facematch_log:
            facematch_log.status = RiderFaceMatchLog.Status.SUCCESS
            facematch_log.is_match = True
            facematch_log.similarity = similarity
            facematch_log.raw_response = raw_response
            facematch_log.save(
                update_fields=[
                    "status",
                    "is_match",
                    "similarity",
                    "raw_response",
                    "updated_at",
                ]
            )

        _publish_to_ably_channel(
            channel_name,
            "facematch_result",
            {
                "status": "success",
                "matched": True,
                "similarity": similarity,
                "message": "Face match verification successful.",
            },
        )
    else:
        logger.warning(
            "Face match FAILED for rider %s (similarity=%.2f, error=%s)",
            rider.rider_id,
            similarity,
            error_message,
        )
        # Block / unauthorize the rider
        rider.face_verification_required = True
        rider.is_authorized = False
        rider.status = Rider.Status.OFFLINE
        rider.save(
            update_fields=[
                "face_verification_required",
                "is_authorized",
                "status",
            ]
        )

        # Deactivate all active sessions to force logout
        RiderSession.objects.filter(rider=rider, is_active=True).update(is_active=False)

        if facematch_log:
            facematch_log.status = RiderFaceMatchLog.Status.FAILED
            facematch_log.is_match = False
            facematch_log.similarity = similarity
            facematch_log.raw_response = raw_response
            facematch_log.error_message = error_message
            facematch_log.save(
                update_fields=[
                    "status",
                    "is_match",
                    "similarity",
                    "raw_response",
                    "error_message",
                    "updated_at",
                ]
            )

        _publish_to_ably_channel(
            channel_name,
            "facematch_result",
            {
                "status": "failed",
                "matched": False,
                "similarity": similarity,
                "action": "logout",
                "message": "Face match verification failed. Your account has been unauthorized.",
            },
        )


@shared_task
def trigger_monthly_face_verification_task(
    days_threshold: int = 30, rider_id: str = None
):
    """
    Periodic / monthly background task:
    Identifies active independent riders due for face verification (last_face_verified_at
    is None or older than `days_threshold` days, or created > days_threshold days ago if never verified).
    Marks face_verification_required=True, deauthorizes job assignment (is_authorized=False),
    and publishes real-time Ably event 'facematch_required' to channel 'facematch:<rider_id>'.
    """
    from dispatcher.models import Rider

    now = timezone.now()
    cutoff = now - timedelta(days=days_threshold)

    query = Rider.objects.filter(
        is_independent_rider=True,
        is_active=True,
        is_deleted=False,
        is_authorized=True,
        face_verification_required=False,
    )

    if rider_id:
        import uuid

        try:
            uuid.UUID(str(rider_id))
            is_uuid = True
        except (ValueError, AttributeError, TypeError):
            is_uuid = False

        if is_uuid:
            query = query.filter(Q(rider_id=rider_id) | Q(id=rider_id))
        else:
            query = query.filter(rider_id=rider_id)
    else:
        # Riders whose last_face_verified_at is older than cutoff,
        # or who have never verified and whose registration was on or before cutoff
        query = query.filter(
            Q(last_face_verified_at__isnull=False, last_face_verified_at__lte=cutoff)
            | Q(last_face_verified_at__isnull=True, created_at__lte=cutoff)
        )

    due_riders = list(query)
    logger.info(
        "Found %d independent riders due for monthly face verification (threshold=%d days)",
        len(due_riders),
        days_threshold,
    )

    from .models import RiderDocument, RiderFaceMatchLog

    processed_ids = []
    for rider in due_riders:
        rider.face_verification_required = True
        rider.is_authorized = False
        rider.save(update_fields=["face_verification_required", "is_authorized"])

        # Fetch reference profile photo if exists
        ref_doc = (
            RiderDocument.objects.filter(
                rider=rider, doc_type=RiderDocument.DocType.PROFILE_PHOTO
            )
            .order_by("-created_at")
            .first()
        )
        ref_photo_url = (
            ref_doc.file_url if ref_doc and ref_doc.file_url else (rider.avatar or "")
        )

        # Record requested face verification audit log
        log = RiderFaceMatchLog.objects.create(
            rider=rider,
            trigger_type=RiderFaceMatchLog.TriggerType.MONTHLY_CRON,
            status=RiderFaceMatchLog.Status.REQUESTED,
            reference_photo_url=ref_photo_url,
            selfie_url="",
        )

        channel_name = f"facematch:{rider.rider_id or rider.id}"
        payload = {
            "action": "face_verification_required",
            "rider_id": rider.rider_id,
            "log_id": str(log.id),
            "due_date": now.isoformat(),
            "reason": "monthly_verification",
        }
        _publish_to_ably_channel(channel_name, "facematch_required", payload)
        processed_ids.append(rider.rider_id or str(rider.id))
        logger.info(
            "Triggered monthly face verification for rider %s (log=%s) on channel %s",
            rider.rider_id,
            log.id,
            channel_name,
        )

    return {
        "processed_count": len(processed_ids),
        "due_riders": processed_ids,
    }


