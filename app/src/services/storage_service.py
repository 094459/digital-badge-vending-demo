"""
Storage service that abstracts file storage between local filesystem and S3.
Uses S3 when S3_BUCKET env var is set, otherwise falls back to local filesystem.
"""
import os
import boto3
from io import BytesIO
from botocore.config import Config


class StorageService:
    """Unified storage interface for local filesystem and S3"""

    def __init__(self):
        self.bucket = os.getenv('S3_BUCKET')
        self.s3_prefix = os.getenv('S3_PREFIX', '')
        if self.bucket:
            region = os.getenv('AWS_REGION', 'eu-west-1')
            self.s3 = boto3.client('s3', region_name=region, config=Config(read_timeout=60))
            print(f"[Storage] Using S3 bucket: {self.bucket}")
        else:
            self.s3 = None
            print("[Storage] Using local filesystem")

    def is_s3(self):
        return self.s3 is not None

    def _s3_key(self, relative_path):
        """Convert a relative path like 'badges/badge_123.png' to an S3 key"""
        key = relative_path.lstrip('/')
        if self.s3_prefix:
            key = f"{self.s3_prefix.strip('/')}/{key}"
        return key

    def save_bytes(self, data: bytes, relative_path: str, local_folder: str = None):
        """
        Save bytes to storage.

        Args:
            data: File content as bytes
            relative_path: Path relative to storage root, e.g. 'badges/badge_123.png'
            local_folder: Local base folder (used only for filesystem fallback)
        """
        if self.is_s3():
            key = self._s3_key(relative_path)
            content_type = 'image/png' if relative_path.endswith('.png') else 'application/octet-stream'
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        else:
            if not local_folder:
                raise ValueError("local_folder required for filesystem storage")
            filename = os.path.basename(relative_path)
            filepath = os.path.join(local_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(data)

    def save_pil_image(self, img, relative_path: str, local_folder: str = None, fmt: str = 'PNG'):
        """
        Save a PIL Image to storage.

        Args:
            img: PIL Image object
            relative_path: Path relative to storage root
            local_folder: Local base folder (filesystem fallback)
            fmt: Image format (default PNG)
        """
        buf = BytesIO()
        img.save(buf, format=fmt)
        self.save_bytes(buf.getvalue(), relative_path, local_folder)

    def load_bytes(self, relative_path: str, local_folder: str = None) -> bytes:
        """
        Load file bytes from storage.

        Args:
            relative_path: Path relative to storage root
            local_folder: Local base folder (filesystem fallback)

        Returns:
            File content as bytes, or None if not found
        """
        if self.is_s3():
            try:
                key = self._s3_key(relative_path)
                response = self.s3.get_object(Bucket=self.bucket, Key=key)
                return response['Body'].read()
            except self.s3.exceptions.NoSuchKey:
                return None
        else:
            if not local_folder:
                return None
            filename = os.path.basename(relative_path)
            filepath = os.path.join(local_folder, filename)
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    return f.read()
            return None

    def load_pil_image(self, relative_path: str, local_folder: str = None):
        """
        Load a PIL Image from storage.

        Returns:
            PIL Image or None if not found
        """
        from PIL import Image
        data = self.load_bytes(relative_path, local_folder)
        if data:
            return Image.open(BytesIO(data))
        return None

    def delete(self, relative_path: str, local_folder: str = None):
        """
        Delete a file from storage.

        Args:
            relative_path: Path relative to storage root
            local_folder: Local base folder (filesystem fallback)
        """
        if self.is_s3():
            key = self._s3_key(relative_path)
            self.s3.delete_object(Bucket=self.bucket, Key=key)
        else:
            if not local_folder:
                return
            filename = os.path.basename(relative_path)
            filepath = os.path.join(local_folder, filename)
            if os.path.exists(filepath):
                os.remove(filepath)

    def exists(self, relative_path: str, local_folder: str = None) -> bool:
        """Check if a file exists in storage."""
        if self.is_s3():
            try:
                key = self._s3_key(relative_path)
                self.s3.head_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:
                return False
        else:
            if not local_folder:
                return False
            filename = os.path.basename(relative_path)
            filepath = os.path.join(local_folder, filename)
            return os.path.exists(filepath)

    def file_path_to_relative(self, file_path: str) -> str:
        """
        Convert a stored file_path like '/static/badges/badge_123.png'
        to a relative storage path like 'badges/badge_123.png'
        """
        return file_path.replace('/static/', '')
