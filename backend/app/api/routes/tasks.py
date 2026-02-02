"""
Routes pour le monitoring des tâches Celery.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from celery.result import AsyncResult

from app.celery_app import celery_app

router = APIRouter()


# =================== SCHEMAS ===================

class TaskStatusResponse(BaseModel):
    """Schéma de réponse pour le statut d'une tâche."""
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


# =================== ROUTES ===================

@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Obtenir le statut d'une tâche Celery."""
    
    result = AsyncResult(task_id, app=celery_app)
    
    response = TaskStatusResponse(
        task_id=task_id,
        status=result.status,
    )
    
    if result.ready():
        if result.successful():
            response.result = result.result
        else:
            response.error = str(result.result)
    
    return response


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_task(task_id: str):
    """Annuler une tâche en attente."""
    
    celery_app.control.revoke(task_id, terminate=True)


@router.get("/")
async def list_active_tasks():
    """Lister les tâches actives."""
    
    inspect = celery_app.control.inspect()
    
    active = inspect.active() or {}
    scheduled = inspect.scheduled() or {}
    reserved = inspect.reserved() or {}
    
    return {
        "active": active,
        "scheduled": scheduled,
        "reserved": reserved,
    }
