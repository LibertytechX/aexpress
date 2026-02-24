import firebase_admin
from firebase_admin import credentials
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

def initialize_firebase():
    """
    Initialize Firebase Admin SDK.
    Uses firebase_key.json in the BASE_DIR.
    """
    if not firebase_admin._apps:
        try:
            cred_path = os.path.join(settings.BASE_DIR, "firebase_key.json")
            if not os.path.exists(cred_path):
                logger.warning(f"Firebase credentials not found at {cred_path}. Push notifications will fail.")
                return

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")

# Initialize when the module is imported
initialize_firebase()
