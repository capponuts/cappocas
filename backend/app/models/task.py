"""
Modèle pour le suivi des tâches Celery.
"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    """Statut d'une tâche."""
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskType(str, enum.Enum):
    """Type de tâche."""
    POST_LISTING = "post_listing"
    LOGIN_PLATFORM = "login_platform"
    DELETE_LISTING = "delete_listing"
    UPDATE_LISTING = "update_listing"


class Task(Base):
    """Suivi des tâches Celery."""
    
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    celery_task_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Type et statut
    task_type = Column(Enum(TaskType), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    
    # Références
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=True)
    platform = Column(String(50), nullable=True)  # leboncoin, vinted
    
    # Résultat
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    traceback = Column(Text, nullable=True)
    
    # Tentatives
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Task {self.celery_task_id} - {self.status.value}>"
