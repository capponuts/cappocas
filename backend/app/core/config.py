"""
Configuration de l'application via variables d'environnement.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configuration principale de l'application."""
    
    # ===================
    # BASE DE DONNÉES
    # ===================
    DATABASE_URL: str = Field(
        default="postgresql://cappocas:cappocas_secret@localhost:5432/cappocas_db"
    )
    
    # ===================
    # REDIS
    # ===================
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # ===================
    # MINIO
    # ===================
    MINIO_ENDPOINT: str = Field(default="localhost:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadmin123")
    MINIO_BUCKET: str = Field(default="cappocas-images")
    MINIO_SECURE: bool = Field(default=False)
    
    # ===================
    # TELEGRAM
    # ===================
    TELEGRAM_BOT_TOKEN: str = Field(default="")
    TELEGRAM_CHAT_ID: str = Field(default="")
    
    # ===================
    # SÉCURITÉ
    # ===================
    SECRET_KEY: str = Field(default="change_this_secret_key")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)
    
    # ===================
    # CORS
    # ===================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )
    
    # ===================
    # PROXIES
    # ===================
    PROXY_LIST_FILE: str = Field(default="/app/config/proxies.txt")
    
    # ===================
    # CREDENTIALS PLATEFORMES
    # ===================
    LEBONCOIN_EMAIL: str = Field(default="")
    LEBONCOIN_PASSWORD: str = Field(default="")
    VINTED_EMAIL: str = Field(default="")
    VINTED_PASSWORD: str = Field(default="")
    
    # ===================
    # DÉLAIS ANTI-BAN
    # ===================
    MIN_DELAY_BETWEEN_POSTS: int = Field(default=300)
    MAX_DELAY_BETWEEN_POSTS: int = Field(default=900)
    MIN_DELAY_BETWEEN_ACTIONS: int = Field(default=2)
    MAX_DELAY_BETWEEN_ACTIONS: int = Field(default=5)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instance singleton
settings = Settings()
