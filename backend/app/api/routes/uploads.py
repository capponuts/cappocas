"""
Routes pour l'upload de fichiers.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.responses import Response
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.listing import ListingImage
from app.services.minio_service import minio_service

router = APIRouter()


@router.get("/view/{image_key:path}")
async def view_image(image_key: str):
    """Router pour afficher une image via le backend (proxy MinIO)."""
    try:
        response = minio_service.client.get_object(minio_service.bucket, image_key)
        content = response.read()
        return Response(content=content, media_type=response.headers.get('content-type', 'image/jpeg'))
    except Exception:
        raise HTTPException(status_code=404, detail="Image non trouvée")


# =================== SCHEMAS ===================

class ImageUploadResponse(BaseModel):
    """Schéma de réponse pour un upload d'image."""
    id: int
    filename: str
    original_filename: str
    minio_key: str
    url: str
    size: int
    mime_type: str


# =================== ROUTES ===================

@router.post("/images", response_model=List[ImageUploadResponse])
async def upload_images(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploader une ou plusieurs images.
    
    Les images sont stockées dans MinIO et une référence est créée
    en base de données pour pouvoir les associer à une annonce.
    """
    
    # Vérifier le type de fichier
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    max_size = 10 * 1024 * 1024  # 10 MB
    
    uploaded_images = []
    
    for file in files:
        # Vérifier le type MIME
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type de fichier non supporté: {file.content_type}"
            )
        
        # Lire le contenu
        content = await file.read()
        file_size = len(content)
        
        # Vérifier la taille
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fichier trop volumineux: {file.filename}"
            )
        
        # Reset le curseur pour l'upload
        await file.seek(0)
        
        # Upload vers MinIO
        try:
            minio_key = minio_service.upload_file(
                file=file.file,
                filename=file.filename,
                content_type=file.content_type,
                size=file_size,
            )
            
            # Obtenir l'URL
            url = minio_service.get_url(minio_key)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur d'upload: {str(e)}"
            )
        
        # Créer l'entrée en base de données
        image = ListingImage(
            listing_id=None,  # Sera associé plus tard
            filename=minio_key.split("/")[-1],
            original_filename=file.filename,
            minio_key=minio_key,
            url=url,
            size=file_size,
            mime_type=file.content_type,
        )
        
        db.add(image)
        await db.commit()
        await db.refresh(image)
        
        uploaded_images.append(ImageUploadResponse(
            id=image.id,
            filename=image.filename,
            original_filename=image.original_filename,
            minio_key=image.minio_key,
            url=url,
            size=image.size,
            mime_type=image.mime_type,
        ))
    
    return uploaded_images


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Supprimer une image."""
    
    from sqlalchemy import select
    
    result = await db.execute(
        select(ListingImage).where(ListingImage.id == image_id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image non trouvée"
        )
    
    # Supprimer de MinIO
    minio_service.delete_file(image.minio_key)
    
    # Supprimer de la base de données
    await db.delete(image)
    await db.commit()
