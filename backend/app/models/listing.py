"""
Modèle pour les annonces.
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, 
    DateTime, Enum, ForeignKey, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ListingStatus(str, enum.Enum):
    """Statut d'une annonce."""
    DRAFT = "draft"
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"


class Listing(Base):
    """Modèle d'une annonce à publier."""
    
    __tablename__ = "listings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Informations de l'annonce
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String(100), nullable=True)
    condition = Column(String(50), nullable=True)  # neuf, très bon état, etc.
    location = Column(String(255), nullable=True)
    
    # Plateformes cibles
    post_to_leboncoin = Column(Boolean, default=True)
    post_to_vinted = Column(Boolean, default=True)
    
    # Statuts par plateforme
    leboncoin_status = Column(Enum(ListingStatus), default=ListingStatus.DRAFT)
    leboncoin_url = Column(String(500), nullable=True)
    leboncoin_posted_at = Column(DateTime, nullable=True)
    leboncoin_error = Column(Text, nullable=True)
    
    vinted_status = Column(Enum(ListingStatus), default=ListingStatus.DRAFT)
    vinted_url = Column(String(500), nullable=True)
    vinted_posted_at = Column(DateTime, nullable=True)
    vinted_error = Column(Text, nullable=True)
    
    # Planification
    scheduled_at = Column(DateTime, nullable=True)
    
    # Métadonnées spécifiques aux plateformes (catégories, etc.)
    leboncoin_metadata = Column(JSON, nullable=True)
    vinted_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    user = relationship("User", back_populates="listings")
    images = relationship("ListingImage", back_populates="listing", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Listing {self.title}>"


class ListingImage(Base):
    """Image associée à une annonce."""
    
    __tablename__ = "listing_images"
    
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    
    # Informations de l'image
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    minio_key = Column(String(500), nullable=False)  # Clé dans MinIO
    url = Column(String(500), nullable=True)  # URL publique
    size = Column(Integer, nullable=True)  # Taille en bytes
    mime_type = Column(String(100), nullable=True)
    order = Column(Integer, default=0)  # Ordre d'affichage
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    listing = relationship("Listing", back_populates="images")
    
    def __repr__(self):
        return f"<ListingImage {self.filename}>"
