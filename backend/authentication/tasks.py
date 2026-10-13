from celery import shared_task
from .models import User
from .emails import (
    send_onboarding_email,
    send_password_reset_otp_to_email,
    send_mobile_password_reset_email,
    prep_user_for_otp,
)
from .services import OTPService
import logging

logger = logging.getLogger(__name__)


@shared_task(name="authentication.tasks.send_onboarding_email_task")
def send_onboarding_email_task(user_id):
    """
    Celery task to send onboarding email to a user.
    """
    try:
        user = User.objects.get(id=user_id)
        return send_onboarding_email(user)
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found for onboarding email task")
        return False
    except Exception as e:
        logger.error(f"Error in send_onboarding_email_task: {str(e)}")
        return False


@shared_task(name="authentication.tasks.send_password_reset_otp_task")
def send_password_reset_otp_task(user_id, is_mobile=False):
    """
    Celery task to send password reset OTP to a user via both email and phone SMS.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found for password reset OTP task")
        return False
    except Exception as e:
        logger.error(f"Error fetching user in send_password_reset_otp_task: {str(e)}")
        return False

    if not user.password_reset_token:
        prep_user_for_otp(user)

    email_sent = False
    sms_sent = False

    if user.email:
        try:
            if is_mobile:
                send_mobile_password_reset_email(user, user.password_reset_token)
            else:
                send_password_reset_otp_to_email(user)
            logger.info(
                f"{'Mobile password' if is_mobile else 'Password'} reset email sent to {user.email}"
            )
            email_sent = True
        except Exception as e:
            logger.error(
                f"Failed to send {'mobile ' if is_mobile else ''}password reset email to {user.email}: {str(e)}"
            )

    if user.phone:
        try:
            OTPService.send_sms_otp(phone=user.phone, otp=user.password_reset_token)
            logger.info(f"Mobile password reset SMS sent to {user.phone}")
            sms_sent = True
        except Exception as e:
            logger.error(f"Failed to send mobile reset SMS to {user.phone}: {str(e)}")

    return {"email_sent": email_sent, "sms_sent": sms_sent}


@shared_task(name="authentication.tasks.send_mobile_password_reset_otp_task")
def send_mobile_password_reset_otp_task(user_id):
    """
    Celery task to send mobile password reset OTP to a user via both email and phone SMS.
    """
    return send_password_reset_otp_task(user_id, is_mobile=True)

