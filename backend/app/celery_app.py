"""
Configuration Celery pour les tâches asynchrones.
"""

from celery import Celery

from app.core.config import settings

# Créer l'application Celery
celery_app = Celery(
    "cappocas",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.posting_tasks"],
)

# Configuration Celery
celery_app.conf.update(
    # Sérialisation
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="Europe/Paris",
    enable_utc=True,
    
    # Résultats
    result_expires=3600 * 24,  # 24 heures
    
    # Tâches
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max par tâche
    task_soft_time_limit=540,  # Warning à 9 minutes
    
    # Retry
    task_default_retry_delay=60,  # 1 minute entre les retries
    task_max_retries=3,
    
    # Rate limiting (anti-ban)
    task_default_rate_limit="5/m",  # 5 tâches par minute max
    
    # Worker
    worker_prefetch_multiplier=1,  # Une tâche à la fois
    worker_concurrency=2,  # 2 workers max
    
    # Beat scheduler (tâches planifiées)
    beat_schedule={
        "check-scheduled-listings": {
            "task": "app.tasks.posting_tasks.process_scheduled_listings",
            "schedule": 60.0,  # Vérifier toutes les minutes
        },
        "cleanup-old-screenshots": {
            "task": "app.tasks.posting_tasks.cleanup_screenshots",
            "schedule": 3600.0,  # Nettoyer toutes les heures
        },
    },
)
