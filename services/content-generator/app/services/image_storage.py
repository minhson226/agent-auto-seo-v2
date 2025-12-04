"""Image storage service using S3/MinIO.

Supports both real S3/MinIO connections and mock mode for testing.
In mock mode, images are stored in memory instead of real object storage.
"""

import logging
import uuid
from typing import BinaryIO, Dict, Optional

import aioboto3
from botocore.config import Config

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ImageStorageService:
    """Service for storing and retrieving images from S3/MinIO.

    Supports mock mode for testing when S3/MinIO is not available.
    In mock mode, images are stored in memory for inspection during tests.

    Mock mode is enabled when:
    - mock_mode=True is passed to constructor, OR
    - S3_ENDPOINT starts with 'mock://'
    """

    def __init__(self, mock_mode: bool = False):
        """Initialize the storage service.

        Args:
            mock_mode: If True, operates in mock mode without real S3 connection.
                      Also enabled automatically when S3_ENDPOINT starts with 'mock://'.
        """
        self.endpoint_url = settings.S3_ENDPOINT
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.bucket = settings.S3_BUCKET_IMAGES
        self.region = settings.S3_REGION
        self._session: Optional[aioboto3.Session] = None
        # Mock mode is enabled by parameter OR by URL prefix
        self._mock_mode = mock_mode or self.endpoint_url.startswith("mock://")
        self._mock_storage: Dict[str, bytes] = {}  # Store images in mock mode

    @property
    def mock_mode(self) -> bool:
        """Check if service is in mock mode."""
        return self._mock_mode

    @property
    def mock_storage(self) -> Dict[str, bytes]:
        """Get mock storage dict (for testing in mock mode)."""
        return self._mock_storage

    def clear_storage(self) -> None:
        """Clear the mock storage (for testing)."""
        self._mock_storage = {}

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

        In mock mode, images are stored in memory.

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

        if self._mock_mode:
            # In mock mode, store in memory
            self._mock_storage[storage_path] = file_content
            logger.info(f"Mock uploaded image to {storage_path}")
            return storage_path

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

        In mock mode, removes the image from memory storage.

        Args:
            storage_path: The storage path of the image to delete

        Returns:
            True if deletion was successful
        """
        if self._mock_mode:
            # In mock mode, delete from memory
            if storage_path in self._mock_storage:
                del self._mock_storage[storage_path]
                logger.info(f"Mock deleted image from {storage_path}")
                return True
            return False

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

        In mock mode, returns a mock URL.

        Args:
            storage_path: The storage path of the image
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL for the image
        """
        if self._mock_mode:
            # Return mock URL
            return f"mock://storage/{storage_path}?expires={expires_in}"

        async with self.session.client("s3", **self._get_client_config()) as s3:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": storage_path},
                ExpiresIn=expires_in,
            )
            return url

    async def ensure_bucket_exists(self) -> None:
        """Ensure the bucket exists, create if not.

        In mock mode, this is a no-op.
        """
        if self._mock_mode:
            logger.info(f"Mock mode - bucket {self.bucket} assumed to exist")
            return

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
