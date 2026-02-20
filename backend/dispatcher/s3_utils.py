import os
import uuid
import boto3
import logging
import traceback
from typing import IO

logger = logging.getLogger(__name__)


def get_aws_s3_client():
    """Get AWS S3 client"""
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            region_name=os.getenv("AWS_S3_REGION_NAME", "eu-north-1"),
        )
        return s3_client
    except Exception as e:
        logger.error(f"Error creating AWS S3 client: {e}")
        raise


def upload_image_file_to_s3(
    file_obj: IO, filename: str, folder: str = "uploads"
) -> str:
    """Uploads an image file to AWS S3 bucket"""
    try:
        s3_client = get_aws_s3_client()
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"{folder}/{uuid.uuid4()}{file_extension}"
        s3_client.upload_fileobj(
            file_obj,
            os.getenv("AWS_STORAGE_BUCKET_NAME", "secourhub"),
            unique_filename,
            ExtraArgs={
                "ContentType": f"image/{file_extension.strip('.')}",
            },
        )
        public_url = f"https://{os.getenv('AWS_STORAGE_BUCKET_NAME', 'secourhub')}.s3.{os.getenv('AWS_S3_REGION_NAME', 'us-east-1')}.amazonaws.com/{unique_filename}"
        return public_url
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error uploading image file to S3: {e}")
        return ""


def upload_document_to_s3(
    file_obj: IO, filename: str, user_type: str, document_type: str
) -> str:
    """Upload document to S3 with organized folder structure"""
    folder = f"documents/{user_type}/{document_type}"
    return upload_image_file_to_s3(file_obj, filename, folder)


def generate_presigned_url(object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object"""
    s3_client = get_aws_s3_client()
    try:
        response = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": os.getenv("AWS_STORAGE_BUCKET_NAME", "secourhub"),
                "Key": object_name,
            },
            ExpiresIn=expiration,
        )
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        return None

    return response
