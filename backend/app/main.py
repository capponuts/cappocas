"""
Cappocas - Application principale FastAPI
Automatisation de postage d'annonces sur Leboncoin et Vinted
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.core.config import settings
from app.core.database import engine, Base
from app.services.minio_service import minio_service
from app.services.discord_service import discord_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # Startup
    print("🚀 Démarrage de Cappocas...")
    
    # Créer les tables de la base de données
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Base de données initialisée")
    
    # Initialiser le bucket MinIO
    await minio_service.init_bucket()
    print("✅ Stockage MinIO initialisé")
    
    # Notification Discord de démarrage
    await discord_service.notify_app_start()
    print("✅ Notification Discord envoyée")
    
    yield
    
    # Shutdown
    print("👋 Arrêt de Cappocas...")
    await engine.dispose()


# Créer l'application FastAPI
app = FastAPI(
    title="Cappocas",
    description="API d'automatisation de postage d'annonces sur Leboncoin et Vinted",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monter les fichiers statiques (uploads)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Inclure les routes API
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Route racine - Health check."""
    return {
        "status": "ok",
        "app": "Cappocas",
        "version": "1.0.0",
        "message": "API d'automatisation d'annonces"
    }


@app.get("/health")
async def health_check():
    """Vérification de santé de l'application."""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "minio": "connected"
    }
