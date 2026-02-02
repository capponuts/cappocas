"""
Routes pour la gestion des annonces.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.listing import Listing, ListingImage, ListingStatus
from app.tasks.posting_tasks import post_to_vinted, post_to_leboncoin

router = APIRouter()


# =================== SCHEMAS ===================

class ListingImageResponse(BaseModel):
    """Schéma de réponse pour une image."""
    id: int
    filename: str
    url: Optional[str]
    order: int
    
    class Config:
        from_attributes = True


class ListingCreate(BaseModel):
    """Schéma pour créer une annonce."""
    title: str
    description: str
    price: float
    category: Optional[str] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    post_to_leboncoin: bool = True
    post_to_vinted: bool = True
    scheduled_at: Optional[datetime] = None
    image_ids: List[int] = []


class ListingUpdate(BaseModel):
    """Schéma pour modifier une annonce."""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    post_to_leboncoin: Optional[bool] = None
    post_to_vinted: Optional[bool] = None
    scheduled_at: Optional[datetime] = None


class ListingResponse(BaseModel):
    """Schéma de réponse pour une annonce."""
    id: int
    title: str
    description: str
    price: float
    category: Optional[str]
    condition: Optional[str]
    location: Optional[str]
    post_to_leboncoin: bool
    post_to_vinted: bool
    leboncoin_status: ListingStatus
    leboncoin_url: Optional[str]
    vinted_status: ListingStatus
    vinted_url: Optional[str]
    scheduled_at: Optional[datetime]
    created_at: datetime
    images: List[ListingImageResponse]
    
    class Config:
        from_attributes = True


# =================== ROUTES ===================

@router.get("/", response_model=List[ListingResponse])
async def get_listings(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtenir toutes les annonces de l'utilisateur."""
    
    result = await db.execute(
        select(Listing)
        .where(Listing.user_id == int(current_user["user_id"]))
        .options(selectinload(Listing.images))
        .order_by(Listing.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    listings = result.scalars().all()
    return [ListingResponse.model_validate(listing) for listing in listings]


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtenir une annonce spécifique."""
    
    result = await db.execute(
        select(Listing)
        .where(
            Listing.id == listing_id,
            Listing.user_id == int(current_user["user_id"])
        )
        .options(selectinload(Listing.images))
    )
    
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annonce non trouvée"
        )
    
    return ListingResponse.model_validate(listing)


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    listing_data: ListingCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Créer une nouvelle annonce."""
    
    user_id = int(current_user["user_id"])
    
    # Créer l'annonce
    listing = Listing(
        user_id=user_id,
        title=listing_data.title,
        description=listing_data.description,
        price=listing_data.price,
        category=listing_data.category,
        condition=listing_data.condition,
        location=listing_data.location,
        post_to_leboncoin=listing_data.post_to_leboncoin,
        post_to_vinted=listing_data.post_to_vinted,
        scheduled_at=listing_data.scheduled_at,
    )
    
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    
    # Associer les images si fournies
    if listing_data.image_ids:
        result = await db.execute(
            select(ListingImage)
            .where(ListingImage.id.in_(listing_data.image_ids))
        )
        images = result.scalars().all()
        
        for image in images:
            image.listing_id = listing.id
        
        await db.commit()
    
    # Recharger avec les images
    await db.refresh(listing)
    
    return ListingResponse.model_validate(listing)


@router.put("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: int,
    listing_data: ListingUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Modifier une annonce."""
    
    result = await db.execute(
        select(Listing)
        .where(
            Listing.id == listing_id,
            Listing.user_id == int(current_user["user_id"])
        )
        .options(selectinload(Listing.images))
    )
    
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annonce non trouvée"
        )
    
    # Mettre à jour les champs
    update_data = listing_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(listing, field, value)
    
    await db.commit()
    await db.refresh(listing)
    
    return ListingResponse.model_validate(listing)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Supprimer une annonce."""
    
    result = await db.execute(
        select(Listing)
        .where(
            Listing.id == listing_id,
            Listing.user_id == int(current_user["user_id"])
        )
    )
    
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annonce non trouvée"
        )
    
    await db.delete(listing)
    await db.commit()


@router.post("/{listing_id}/publish")
async def publish_listing(
    listing_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Publier une annonce sur les plateformes sélectionnées."""
    
    result = await db.execute(
        select(Listing)
        .where(
            Listing.id == listing_id,
            Listing.user_id == int(current_user["user_id"])
        )
        .options(selectinload(Listing.images))
    )
    
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annonce non trouvée"
        )
    
    # Récupérer les chemins des images
    image_paths = [img.minio_key for img in listing.images]
    
    tasks_launched = []
    
    # Lancer les tâches de postage
    if listing.post_to_vinted:
        task = post_to_vinted.delay(
            listing_id=listing.id,
            title=listing.title,
            description=listing.description,
            price=listing.price,
            images=image_paths,
            email=settings.VINTED_EMAIL,
            password=settings.VINTED_PASSWORD,
            category=listing.category,
            condition=listing.condition,
        )
        listing.vinted_status = ListingStatus.PENDING
        tasks_launched.append({"platform": "vinted", "task_id": task.id})
    
    if listing.post_to_leboncoin:
        task = post_to_leboncoin.delay(
            listing_id=listing.id,
            title=listing.title,
            description=listing.description,
            price=listing.price,
            images=image_paths,
            email=settings.LEBONCOIN_EMAIL,
            password=settings.LEBONCOIN_PASSWORD,
            category=listing.category,
            condition=listing.condition,
            location=listing.location,
        )
        listing.leboncoin_status = ListingStatus.PENDING
        tasks_launched.append({"platform": "leboncoin", "task_id": task.id})
    
    await db.commit()
    
    return {
        "message": "Publication lancée",
        "tasks": tasks_launched
    }
