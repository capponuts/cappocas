"""
Routes d'authentification.
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    get_current_user
)
from app.core.config import settings
from app.models.user import User

router = APIRouter()


# =================== SCHEMAS ===================

class UserCreate(BaseModel):
    """Schéma pour créer un utilisateur."""
    email: EmailStr
    username: str
    password: str
    telegram_chat_id: Optional[str] = None


class UserLogin(BaseModel):
    """Schéma pour la connexion."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schéma de réponse utilisateur."""
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    telegram_chat_id: Optional[str]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schéma de réponse token."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =================== ROUTES ===================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Créer un nouveau compte utilisateur."""
    
    # Inscriptions désactivées - seul l'admin peut créer des comptes
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Les inscriptions sont désactivées. Contactez l'administrateur."
    )
    
    # Vérifier si l'email existe déjà
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé"
        )
    
    # Vérifier si le username existe déjà
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur est déjà utilisé"
        )
    
    # Créer l'utilisateur
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        telegram_chat_id=user_data.telegram_chat_id,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Créer le token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Se connecter et obtenir un token."""
    
    # Trouver l'utilisateur
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )
    
    # Créer le token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtenir les informations de l'utilisateur connecté."""
    
    result = await db.execute(
        select(User).where(User.id == int(current_user["user_id"]))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return UserResponse.model_validate(user)
