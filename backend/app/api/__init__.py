"""
Routes API de l'application.
"""

from fastapi import APIRouter

from app.api.routes import auth, listings, uploads, tasks, categories

router = APIRouter()

# Inclure les routes
router.include_router(auth.router, prefix="/auth", tags=["Authentification"])
router.include_router(listings.router, prefix="/listings", tags=["Annonces"])
router.include_router(uploads.router, prefix="/uploads", tags=["Uploads"])
router.include_router(tasks.router, prefix="/tasks", tags=["Tâches"])
router.include_router(categories.router, prefix="/categories", tags=["Catégories Vinted"])
