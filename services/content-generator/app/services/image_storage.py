"""Image storage service using S3/MinIO."""

import logging
import uuid
from typing import BinaryIO, Optional

import aioboto3
from botocore.config import Config

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ImageStorageService:
    """Service for storing and retrieving images from S3/MinIO."""

    def __init__(self):
        """Initialize the storage service."""
        self.endpoint_url = settings.S3_ENDPOINT
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.bucket = settings.S3_BUCKET_IMAGES
        self.region = settings.S3_REGION
        self._session: Optional[aioboto3.Session] = None

    @property
    def session(self) -> aioboto3.Session:
        """Get or create aioboto3 session."""
        if self._session is None:
            self._session = aioboto3.Session()
        return self._session

    def _get_client_config(self):
        """Get client configuration."""
        return {
            "endpoint_url": self.endpoint_url,
            "aws_access_key_id": self.access_key,
            "aws_secret_access_key": self.secret_key,
            "region_name": self.region,
            "config": Config(signature_version="s3v4"),
        }

    async def upload_image(
        self,
        article_id: uuid.UUID,
        file_content: bytes,
        original_filename: str,
        content_type: str,
    ) -> str:
        """Upload an image to S3/MinIO.

        Args:
            article_id: The article ID to associate the image with
            file_content: The image file content as bytes
            original_filename: Original filename from upload
            content_type: MIME type of the image

        Returns:
            The storage path of the uploaded image
        """
        # Generate unique filename
        extension = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "jpg"
        unique_filename = f"{uuid.uuid4()}.{extension}"
        storage_path = f"articles/{article_id}/{unique_filename}"

        async with self.session.client("s3", **self._get_client_config()) as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=storage_path,
                Body=file_content,
                ContentType=content_type,
            )
            logger.info(f"Uploaded image to {storage_path}")

        return storage_path

    async def delete_image(self, storage_path: str) -> bool:
        """Delete an image from S3/MinIO.

        Args:
            storage_path: The storage path of the image to delete

        Returns:
            True if deletion was successful
        """
        try:
            async with self.session.client("s3", **self._get_client_config()) as s3:
                await s3.delete_object(
                    Bucket=self.bucket,
                    Key=storage_path,
                )
                logger.info(f"Deleted image from {storage_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete image {storage_path}: {e}")
            return False

    async def get_image_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for an image.

        Args:
            storage_path: The storage path of the image
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL for the image
        """
        async with self.session.client("s3", **self._get_client_config()) as s3:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": storage_path},
                ExpiresIn=expires_in,
            )
            return url

    async def ensure_bucket_exists(self) -> None:
        """Ensure the bucket exists, create if not."""
        try:
            async with self.session.client("s3", **self._get_client_config()) as s3:
                try:
                    await s3.head_bucket(Bucket=self.bucket)
                except Exception:
                    await s3.create_bucket(Bucket=self.bucket)
                    logger.info(f"Created bucket: {self.bucket}")
        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {e}")


# Global instance
image_storage = ImageStorageService()
