"""
Service de stockage MinIO (compatible S3).
"""

import uuid
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class MinIOService:
    """Service pour gérer le stockage des images dans MinIO."""
    
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET
    
    async def init_bucket(self):
        """Initialiser le bucket s'il n'existe pas."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                print(f"✅ Bucket '{self.bucket}' créé")
            else:
                print(f"ℹ️ Bucket '{self.bucket}' existe déjà")
        except S3Error as e:
            print(f"❌ Erreur MinIO: {e}")
            raise
    
    def generate_key(self, filename: str, prefix: str = "images") -> str:
        """Générer une clé unique pour le fichier."""
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        unique_id = uuid.uuid4().hex
        return f"{prefix}/{unique_id}.{ext}" if ext else f"{prefix}/{unique_id}"
    
    def upload_file(
        self, 
        file: BinaryIO, 
        filename: str,
        content_type: str = "image/jpeg",
        size: int = -1,
    ) -> str:
        """
        Uploader un fichier vers MinIO.
        
        Returns:
            str: La clé du fichier dans MinIO
        """
        key = self.generate_key(filename)
        
        try:
            self.client.put_object(
                self.bucket,
                key,
                file,
                length=size,
                content_type=content_type,
            )
            return key
        except S3Error as e:
            print(f"❌ Erreur upload MinIO: {e}")
            raise
    
    def get_url(self, key: str, expires_hours: int = 24) -> str:
        """Obtenir une URL présignée pour accéder au fichier."""
        from datetime import timedelta
        
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                key,
                expires=timedelta(hours=expires_hours),
            )
            return url
        except S3Error as e:
            print(f"❌ Erreur URL MinIO: {e}")
            raise
    
    def delete_file(self, key: str) -> bool:
        """Supprimer un fichier de MinIO."""
        try:
            self.client.remove_object(self.bucket, key)
            return True
        except S3Error as e:
            print(f"❌ Erreur suppression MinIO: {e}")
            return False
    
    def download_file(self, key: str, destination: str) -> bool:
        """Télécharger un fichier depuis MinIO."""
        try:
            self.client.fget_object(self.bucket, key, destination)
            return True
        except S3Error as e:
            print(f"❌ Erreur téléchargement MinIO: {e}")
            return False


# Instance singleton
minio_service = MinIOService()
