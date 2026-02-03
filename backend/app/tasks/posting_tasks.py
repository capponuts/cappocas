"""
Tâches Celery pour le postage des annonces.
"""

import asyncio
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from celery import shared_task

from app.core.config import settings
from app.automation.vinted import VintedAutomation
from app.automation.leboncoin import LeboncoinAutomation
from app.services.minio_service import minio_service
from app.services.discord_service import discord_service
import tempfile
import os


def get_random_proxy() -> Optional[str]:
    """Obtenir un proxy aléatoire depuis le fichier de configuration."""
    proxy_file = Path(settings.PROXY_LIST_FILE)
    
    if not proxy_file.exists():
        return None
    
    with open(proxy_file, "r") as f:
        proxies = [
            line.strip() for line in f 
            if line.strip() and not line.strip().startswith("#")
        ]
    
    if not proxies:
        return None
    
    return random.choice(proxies)


def run_async(coro):
    """Helper pour exécuter des coroutines dans Celery."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # Si on est déjà dans une boucle (peu probable dans un worker Celery standard)
        # on utilise une autre méthode ou on lève une erreur
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    else:
        return loop.run_until_complete(coro)


@shared_task(bind=True, max_retries=3)
def post_to_vinted(
    self,
    listing_id: int,
    title: str,
    description: str,
    price: float,
    images: List[str],
    email: str,
    password: str,
    category: Optional[str] = None,
    category_path: Optional[List[str]] = None,
    condition: Optional[str] = None,
    brand: Optional[str] = None,
    size: Optional[str] = None,
    colors: Optional[List[str]] = None,
    **kwargs
):
    """
    Poster une annonce sur Vinted avec catégorisation automatique.
    
    Args:
        listing_id: ID de l'annonce
        title: Titre
        description: Description
        price: Prix
        images: Chemins des images
        email: Email Vinted
        password: Mot de passe Vinted
        category: Nom de la catégorie
        category_path: Chemin complet de la catégorie Vinted
        condition: État du produit
        brand: Marque
        size: Taille
        colors: Liste des couleurs
    """
    async def _post():
        proxy = get_random_proxy()
        print(f"🚀 [Vinted] Démarrage du postage pour l'annonce {listing_id}", flush=True)
        print(f"DEBUG: title='{title}', price={price}, images={images}", flush=True)
        print(f"DEBUG: settings.VINTED_EMAIL='{email}', proxy='{proxy}'", flush=True)
        
        # Télécharger les images localement pour Playwright
        local_image_paths = []
        temp_dir = tempfile.mkdtemp()
        print(f"📂 [Vinted] Dossier temporaire: {temp_dir}", flush=True)
        
        try:
            for image_key in images:
                local_path = os.path.join(temp_dir, os.path.basename(image_key))
                print(f"📥 [Vinted] Téléchargement de '{image_key}' vers '{local_path}'...", flush=True)
                minio_service.client.fget_object(
                    minio_service.bucket,
                    image_key,
                    local_path
                )
                local_image_paths.append(local_path)
            
            print(f"📸 [Vinted] {len(local_image_paths)} images téléchargées", flush=True)
            
            async with VintedAutomation(proxy=proxy) as vinted:
                # Connexion
                print(f"🔑 [Vinted] Tentative de connexion à {vinted.BASE_URL}...", flush=True)
                
                # Chargement des cookies si le fichier existe
                import json
                cookies = None
                cookie_file = "/app/config/vinted_cookies.json"
                if os.path.exists(cookie_file):
                    print(f"🍪 [Vinted] Chargement des cookies depuis {cookie_file}", flush=True)
                    try:
                        with open(cookie_file, "r") as f:
                            cookies = json.load(f)
                    except Exception as e:
                        print(f"⚠️ [Vinted] Erreur lecture cookies: {e}", flush=True)
                
                login_success = await vinted.login(email, password, cookies=cookies)
                
                if not login_success:
                    print("❌ [Vinted] Échec de connexion", flush=True)
                    raise Exception("Échec de connexion à Vinted")
                
                # ... (rest of the logic)
                print("📝 [Vinted] Envoi de l'annonce...", flush=True)
                result = await vinted.post_listing(
                    title=title,
                    description=description,
                    price=price,
                    images=local_image_paths,
                    category=category,
                    brand=brand,
                    condition=condition,
                    size=size,
                    colors=colors,
                )
                return result
        except Exception as e:
            import traceback
            print(f"💥 [Vinted] Erreur critique: {str(e)}")
            print(traceback.format_exc())
            raise
        finally:
            # Nettoyage
            pass
    
    try:
        result = run_async(_post())
        
        # Notification Discord
        if result.get("success"):
            run_async(discord_service.notify_success(
                listing_title=title,
                platform="vinted",
                url=result.get("url")
            ))
        else:
            run_async(discord_service.notify_failure(
                listing_title=title,
                platform="vinted",
                error=result.get("error", "Erreur inconnue")
            ))
        
        return result
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}"
        stack = traceback.format_exc()
        print(f"💥 [Vinted] Erreur critique: {error_msg}")
        print(stack)
        
        run_async(discord_service.notify_failure(
            listing_title=title,
            platform="vinted",
            error=f"{error_msg}\n{stack[:200]}"
        ))
        
        # Retry avec backoff exponentiel
        retry_delay = 60 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=retry_delay)


@shared_task(bind=True, max_retries=3)
def post_to_leboncoin(
    self,
    listing_id: int,
    title: str,
    description: str,
    price: float,
    images: List[str],
    email: str,
    password: str,
    **kwargs
):
    """
    Poster une annonce sur Leboncoin.
    """
    async def _post():
        proxy = get_random_proxy()
        print(f"🚀 [Leboncoin] Démarrage du postage pour l'annonce {listing_id}")
        
        # Télécharger les images localement
        local_image_paths = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            for image_key in images:
                local_path = os.path.join(temp_dir, os.path.basename(image_key))
                print(f"📥 [Leboncoin] Téléchargement de {image_key}...")
                minio_service.client.fget_object(
                    minio_service.bucket,
                    image_key,
                    local_path
                )
                local_image_paths.append(local_path)
                
            async with LeboncoinAutomation(proxy=proxy) as leboncoin:
                # Connexion
                print("🔑 [Leboncoin] Connexion en cours...")
                login_success = await leboncoin.login(email, password)
                
                if not login_success:
                    print("❌ [Leboncoin] Échec de connexion")
                    raise Exception("Échec de connexion à Leboncoin")
                
                # Délai aléatoire anti-ban
                delay = random.randint(
                    settings.MIN_DELAY_BETWEEN_POSTS,
                    settings.MAX_DELAY_BETWEEN_POSTS
                )
                print(f"⏳ [Leboncoin] Attente anti-ban de {delay} secondes...")
                await asyncio.sleep(delay)
                
                # Poster l'annonce
                print("📝 [Leboncoin] Envoi de l'annonce...")
                result = await leboncoin.post_listing(
                    title=title,
                    description=description,
                    price=price,
                    images=local_image_paths, # Utiliser les chemins locaux
                    **kwargs
                )
                
                if result.get("success"):
                    print(f"✅ [Leboncoin] Succès: {result.get('url')}")
                else:
                    print(f"❌ [Leboncoin] Erreur: {result.get('error')}")
                    
                return result
        except Exception as e:
            print(f"💥 [Leboncoin] Erreur critique: {str(e)}")
            raise
        finally:
            pass
    
    try:
        result = run_async(_post())
        
        # Notification Discord
        if result.get("success"):
            run_async(discord_service.notify_success(
                listing_title=title,
                platform="leboncoin",
                url=result.get("url")
            ))
        else:
            run_async(discord_service.notify_failure(
                listing_title=title,
                platform="leboncoin",
                error=result.get("error", "Erreur inconnue")
            ))
        
        return result
        
    except Exception as e:
        retry_delay = 60 * (2 ** self.request.retries)
        
        run_async(discord_service.notify_failure(
            listing_title=title,
            platform="leboncoin",
            error=str(e)
        ))
        
        raise self.retry(exc=e, countdown=retry_delay)


@shared_task
def process_scheduled_listings():
    """
    Vérifier et traiter les annonces planifiées ou en attente.
    """
    async def _process():
        from app.core.database import AsyncSessionLocal
        from app.models.listing import Listing, ListingStatus
        from sqlalchemy import select, or_
        from sqlalchemy.orm import selectinload
        from datetime import datetime
        
        async with AsyncSessionLocal() as db:
            # Chercher les annonces PENDING ou SCHEDULED
            result = await db.execute(
                select(Listing)
                .where(
                    or_(
                        Listing.vinted_status == ListingStatus.PENDING,
                        Listing.leboncoin_status == ListingStatus.PENDING,
                        Listing.scheduled_at <= datetime.now()
                    )
                )
                .options(selectinload(Listing.images))
            )
            listings = result.scalars().all()
            
            if not listings:
                return
                
            print(f"🔄 [Scheduler] Traitement de {len(listings)} annonces")
            
            for listing in listings:
                image_keys = [img.minio_key for img in listing.images]
                
                # Vinted
                if listing.vinted_status == ListingStatus.PENDING:
                    print(f"🚀 [Scheduler] Envoi Vinted pour: {listing.title}")
                    post_to_vinted.delay(
                        listing.id, listing.title, listing.description, listing.price, 
                        image_keys, settings.VINTED_EMAIL, settings.VINTED_PASSWORD,
                        listing.category, listing.brand, listing.condition, listing.size, listing.colors
                    )
                    listing.vinted_status = ListingStatus.PUBLISHING
                    
                # Leboncoin
                if listing.leboncoin_status == ListingStatus.PENDING:
                    print(f"🚀 [Scheduler] Envoi Leboncoin pour: {listing.title}")
                    post_to_leboncoin.delay(
                        listing.id, listing.title, listing.description, listing.price, 
                        image_keys, settings.LEBONCOIN_EMAIL, settings.LEBONCOIN_PASSWORD
                    )
                    listing.leboncoin_status = ListingStatus.PUBLISHING
            
            await db.commit()
            
    try:
        run_async(_process())
    except Exception as e:
        import traceback
        print(f"❌ [Scheduler] Erreur: {e}")
        print(traceback.format_exc())


@shared_task
def cleanup_screenshots():
    """
    Nettoyer les anciennes captures d'écran.
    """
    screenshots_dir = Path("/app/screenshots")
    
    if not screenshots_dir.exists():
        return
    
    # Supprimer les screenshots de plus de 24h
    cutoff = datetime.now() - timedelta(hours=24)
    
    for screenshot in screenshots_dir.glob("*.png"):
        if datetime.fromtimestamp(screenshot.stat().st_mtime) < cutoff:
            screenshot.unlink()
