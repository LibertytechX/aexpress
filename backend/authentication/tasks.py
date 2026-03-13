from celery import shared_task
from .models import User
from .emails import send_onboarding_email
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
