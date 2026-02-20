import os
import logging
from celery import shared_task
from django.conf import settings
from .models import Rider
from .utils import MailgunEmailService

logger = logging.getLogger(__name__)


@shared_task
def send_onboarding_email_task(email, first_name, password, rider_id=None):
    """
    Background task to send onboarding email.
    """
    try:
        # Send onboarding email
        MailgunEmailService.send_onboarding_email(email, first_name, password)

        if rider_id:
            logger.info(f"Onboarding email sent for rider {rider_id}")
        else:
            logger.info(f"Onboarding email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Error in send_onboarding_email_task: {str(e)}")
        return False


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def upload_rider_documents_to_s3(
    self,
    rider_id,
    avatar_data=None,
    avatar_name=None,
    vehicle_photo_data=None,
    vehicle_photo_name=None,
    driving_license_photo_data=None,
    driving_license_photo_name=None,
    identity_card_photo_data=None,
    identity_card_photo_name=None,
):
    """
    Background task to upload rider documents to S3.
    """
    import base64
    import io
    from .s3_utils import upload_image_file_to_s3

    try:
        rider = Rider.objects.get(id=rider_id)

        # Upload Avatar
        if avatar_data and avatar_name:
            file_content = base64.b64decode(avatar_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(file_obj, avatar_name, "riders/avatars")
            if url:
                rider.avatar = url

        # Upload Vehicle Photo
        if vehicle_photo_data and vehicle_photo_name:
            file_content = base64.b64decode(vehicle_photo_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(
                file_obj, vehicle_photo_name, "riders/vehicles"
            )
            if url:
                rider.vehicle_photo = url

        # Upload License
        if driving_license_photo_data and driving_license_photo_name:
            file_content = base64.b64decode(driving_license_photo_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(
                file_obj, driving_license_photo_name, "riders/license"
            )
            if url:
                rider.driving_license_photo = url

        # Upload ID Card
        if identity_card_photo_data and identity_card_photo_name:
            file_content = base64.b64decode(identity_card_photo_data)
            file_obj = io.BytesIO(file_content)
            url = upload_image_file_to_s3(
                file_obj, identity_card_photo_name, "riders/id_card"
            )
            if url:
                rider.identity_card_photo = url

        rider.save()
        logger.info(f"Successfully uploaded documents for rider {rider_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to upload documents for rider {rider_id}: {str(e)}")
        return False
