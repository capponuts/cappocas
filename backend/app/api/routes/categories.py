"""
Routes API pour la gestion des catégories Vinted.
"""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.category_service import category_service


router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Requête d'analyse de catégorie."""
    title: str
    description: Optional[str] = ""
    category_hint: Optional[str] = None


class CategoryResponse(BaseModel):
    """Réponse avec catégorie."""
    id: int
    name: str
    path: list
    full_path: str
    gender: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Réponse d'analyse."""
    title: str
    description: str
    detected_gender: Optional[str]
    suggested_category: Optional[dict]
    confidence: float
    alternatives: list
    message: Optional[str] = None


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_listing(request: AnalyzeRequest):
    """
    Analyse un titre/description et suggère la meilleure catégorie Vinted.
    
    Utile pour montrer à l'utilisateur quelle catégorie sera sélectionnée
    avant de poster l'annonce.
    """
    result = category_service.suggest_category(
        request.title,
        request.description or "",
        request.category_hint
    )
    
    detected_gender = category_service.detect_gender(
        f"{request.title} {request.description or ''}"
    )
    
    response = {
        "title": request.title,
        "description": request.description or "",
        "detected_gender": detected_gender,
        "confidence": result.get("confidence", 0),
        "alternatives": [],
        "message": result.get("message")
    }
    
    if result.get("category"):
        cat = result["category"]
        response["suggested_category"] = {
            "id": cat.id,
            "name": cat.name,
            "path": cat.path,
            "full_path": " > ".join(cat.path),
            "gender": cat.gender
        }
        
        response["alternatives"] = [
            {
                "id": alt.id,
                "name": alt.name,
                "path": alt.path,
                "full_path": " > ".join(alt.path),
                "gender": alt.gender
            }
            for alt in result.get("alternatives", [])
        ]
    else:
        response["suggested_category"] = None
    
    return response


@router.get("/list")
async def list_categories(
    gender: Optional[str] = Query(None, description="Filtrer par genre (femme, homme, enfant, mixte)"),
    search: Optional[str] = Query(None, description="Rechercher par mot-clé")
):
    """
    Liste toutes les catégories disponibles.
    
    Peut être filtré par genre ou recherche textuelle.
    """
    categories = category_service.get_all_categories()
    
    if gender:
        gender_lower = gender.lower()
        categories = [
            c for c in categories 
            if c["gender"] == gender_lower or c["gender"] == "mixte"
        ]
    
    if search:
        search_lower = search.lower()
        categories = [
            c for c in categories
            if search_lower in c["full_path"].lower() or search_lower in c["name"].lower()
        ]
    
    return {
        "total": len(categories),
        "categories": categories
    }


@router.get("/search")
async def search_categories(
    q: str = Query(..., description="Terme de recherche"),
    limit: int = Query(10, ge=1, le=50, description="Nombre de résultats")
):
    """
    Recherche des catégories par mot-clé.
    """
    results = category_service.search_categories(q, limit)
    
    return {
        "query": q,
        "total": len(results),
        "categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "path": cat.path,
                "full_path": " > ".join(cat.path),
                "gender": cat.gender
            }
            for cat in results
        ]
    }


@router.get("/by-gender/{gender}")
async def categories_by_gender(gender: str):
    """
    Retourne toutes les catégories pour un genre spécifique.
    
    Args:
        gender: femme, homme, enfant ou mixte
    """
    all_categories = category_service.get_all_categories()
    
    gender_lower = gender.lower()
    
    # Grouper par catégorie principale (premier élément du path)
    grouped = {}
    for cat in all_categories:
        if cat["gender"] == gender_lower or cat["gender"] == "mixte":
            main_cat = cat["path"][0] if cat["path"] else "Autre"
            if main_cat not in grouped:
                grouped[main_cat] = []
            grouped[main_cat].append(cat)
    
    return {
        "gender": gender,
        "categories": grouped
    }
