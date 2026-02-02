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
from app.services.telegram_service import telegram_service


def get_random_proxy() -> Optional[str]:
    """Obtenir un proxy aléatoire depuis le fichier de configuration."""
    proxy_file = Path(settings.PROXY_LIST_FILE)
    
    if not proxy_file.exists():
        return None
    
    with open(proxy_file, "r") as f:
        proxies = [line.strip() for line in f if line.strip()]
    
    if not proxies:
        return None
    
    return random.choice(proxies)


def run_async(coro):
    """Helper pour exécuter des coroutines dans Celery."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


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
    **kwargs
):
    """
    Poster une annonce sur Vinted.
    
    Cette tâche est exécutée de manière asynchrone par Celery.
    """
    async def _post():
        proxy = get_random_proxy()
        
        async with VintedAutomation(proxy=proxy) as vinted:
            # Connexion
            login_success = await vinted.login(email, password)
            
            if not login_success:
                raise Exception("Échec de connexion à Vinted")
            
            # Délai aléatoire anti-ban
            delay = random.randint(
                settings.MIN_DELAY_BETWEEN_POSTS,
                settings.MAX_DELAY_BETWEEN_POSTS
            )
            await asyncio.sleep(delay)
            
            # Poster l'annonce
            result = await vinted.post_listing(
                title=title,
                description=description,
                price=price,
                images=images,
                **kwargs
            )
            
            return result
    
    try:
        result = run_async(_post())
        
        # Notification Telegram
        if result.get("success"):
            run_async(telegram_service.notify_success(
                listing_title=title,
                platform="vinted",
                url=result.get("url")
            ))
        else:
            run_async(telegram_service.notify_failure(
                listing_title=title,
                platform="vinted",
                error=result.get("error", "Erreur inconnue")
            ))
        
        return result
        
    except Exception as e:
        # Retry avec backoff exponentiel
        retry_delay = 60 * (2 ** self.request.retries)
        
        run_async(telegram_service.notify_failure(
            listing_title=title,
            platform="vinted",
            error=str(e)
        ))
        
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
        
        async with LeboncoinAutomation(proxy=proxy) as leboncoin:
            # Connexion
            login_success = await leboncoin.login(email, password)
            
            if not login_success:
                raise Exception("Échec de connexion à Leboncoin")
            
            # Délai aléatoire anti-ban
            delay = random.randint(
                settings.MIN_DELAY_BETWEEN_POSTS,
                settings.MAX_DELAY_BETWEEN_POSTS
            )
            await asyncio.sleep(delay)
            
            # Poster l'annonce
            result = await leboncoin.post_listing(
                title=title,
                description=description,
                price=price,
                images=images,
                **kwargs
            )
            
            return result
    
    try:
        result = run_async(_post())
        
        # Notification Telegram
        if result.get("success"):
            run_async(telegram_service.notify_success(
                listing_title=title,
                platform="leboncoin",
                url=result.get("url")
            ))
        else:
            run_async(telegram_service.notify_failure(
                listing_title=title,
                platform="leboncoin",
                error=result.get("error", "Erreur inconnue")
            ))
        
        return result
        
    except Exception as e:
        retry_delay = 60 * (2 ** self.request.retries)
        
        run_async(telegram_service.notify_failure(
            listing_title=title,
            platform="leboncoin",
            error=str(e)
        ))
        
        raise self.retry(exc=e, countdown=retry_delay)


@shared_task
def process_scheduled_listings():
    """
    Vérifier et traiter les annonces planifiées.
    
    Cette tâche est exécutée périodiquement par Celery Beat.
    """
    # TODO: Implémenter la logique de récupération des annonces
    # planifiées depuis la base de données et lancer les tâches
    # de postage appropriées
    pass


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
