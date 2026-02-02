"""
Services de l'application.
"""

from app.services.minio_service import minio_service
from app.services.telegram_service import telegram_service

__all__ = [
    "minio_service",
    "telegram_service",
]
