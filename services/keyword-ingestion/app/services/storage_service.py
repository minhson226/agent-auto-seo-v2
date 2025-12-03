"""Storage service for MinIO/S3."""

import io
import logging
from typing import Optional
from uuid import uuid4

from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class StorageService:
    """Service for storing files in MinIO/S3."""

    def __init__(self):
        self.client: Optional[Minio] = None
        self.bucket = settings.S3_BUCKET

    def _get_client(self) -> Minio:
        """Get or create MinIO client."""
        if self.client is None:
            self.client = Minio(
                settings.S3_ENDPOINT,
                access_key=settings.S3_ACCESS_KEY,
                secret_key=settings.S3_SECRET_KEY,
                secure=settings.S3_USE_SSL,
            )
        return self.client

    async def ensure_bucket(self):
        """Ensure the bucket exists, create if not."""
        try:
            client = self._get_client()
            if not client.bucket_exists(self.bucket):
                client.make_bucket(self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise

    async def upload_file(
        self,
        content: bytes,
        filename: str,
        workspace_id: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to S3/MinIO.

        Args:
            content: File content as bytes
            filename: Original filename
            workspace_id: Workspace ID for organizing files
            content_type: MIME type of the file

        Returns:
            URL/path of the uploaded file
        """
        try:
            await self.ensure_bucket()
            client = self._get_client()

            # Generate unique object name
            file_id = str(uuid4())
            object_name = f"{workspace_id}/{file_id}/{filename}"

            # Upload file
            client.put_object(
                self.bucket,
                object_name,
                io.BytesIO(content),
                len(content),
                content_type=content_type,
            )

            logger.info(f"Uploaded file to: {object_name}")
            return f"s3://{self.bucket}/{object_name}"

        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise ValueError(f"Failed to upload file: {str(e)}")

    async def download_file(self, object_path: str) -> bytes:
        """Download a file from S3/MinIO.

        Args:
            object_path: Path of the object (without s3:// prefix)

        Returns:
            File content as bytes
        """
        try:
            client = self._get_client()

            # Parse object path
            if object_path.startswith("s3://"):
                # Remove s3://bucket/ prefix
                parts = object_path[5:].split("/", 1)
                if len(parts) == 2:
                    object_name = parts[1]
                else:
                    object_name = object_path[5:]
            else:
                object_name = object_path

            response = client.get_object(self.bucket, object_name)
            content = response.read()
            response.close()
            response.release_conn()

            logger.info(f"Downloaded file from: {object_name}")
            return content

        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise ValueError(f"Failed to download file: {str(e)}")

    async def delete_file(self, object_path: str):
        """Delete a file from S3/MinIO.

        Args:
            object_path: Path of the object
        """
        try:
            client = self._get_client()

            # Parse object path
            if object_path.startswith("s3://"):
                parts = object_path[5:].split("/", 1)
                if len(parts) == 2:
                    object_name = parts[1]
                else:
                    object_name = object_path[5:]
            else:
                object_name = object_path

            client.remove_object(self.bucket, object_name)
            logger.info(f"Deleted file: {object_name}")

        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise ValueError(f"Failed to delete file: {str(e)}")
