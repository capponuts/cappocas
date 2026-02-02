"""
Modèle pour les comptes des plateformes (Leboncoin, Vinted).
"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Platform(str, enum.Enum):
    """Plateformes supportées."""
    LEBONCOIN = "leboncoin"
    VINTED = "vinted"


class PlatformAccount(Base):
    """Compte sur une plateforme de vente."""
    
    __tablename__ = "platform_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Plateforme
    platform = Column(Enum(Platform), nullable=False)
    
    # Credentials (chiffrés idéalement)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)  # À chiffrer en production
    
    # Statut
    is_active = Column(Boolean, default=True)
    is_logged_in = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Cookies de session (pour éviter de se reconnecter)
    session_cookies = Column(Text, nullable=True)
    
    # Statistiques
    total_posts = Column(Integer, default=0)
    successful_posts = Column(Integer, default=0)
    failed_posts = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    user = relationship("User", back_populates="platform_accounts")
    
    def __repr__(self):
        return f"<PlatformAccount {self.platform.value}:{self.email}>"
