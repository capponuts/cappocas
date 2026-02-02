"""
Services de l'application.
"""

from app.services.minio_service import minio_service
from app.services.discord_service import discord_service

__all__ = [
    "minio_service",
    "discord_service",
]
