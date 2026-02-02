"""
Service de notification Telegram.
"""

import asyncio
from typing import Optional
import httpx

from app.core.config import settings


class TelegramService:
    """Service pour envoyer des notifications via Telegram."""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    @property
    def is_configured(self) -> bool:
        """Vérifier si le bot est configuré."""
        return bool(self.bot_token and self.chat_id)
    
    async def send_message(
        self, 
        message: str, 
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Envoyer un message Telegram.
        
        Args:
            message: Le message à envoyer
            chat_id: ID du chat (utilise la config par défaut si non spécifié)
            parse_mode: Mode de parsing (HTML ou Markdown)
        
        Returns:
            bool: True si le message a été envoyé avec succès
        """
        if not self.is_configured:
            print("⚠️ Telegram non configuré")
            return False
        
        target_chat = chat_id or self.chat_id
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": target_chat,
                        "text": message,
                        "parse_mode": parse_mode,
                    }
                )
                
                if response.status_code == 200:
                    return True
                else:
                    print(f"❌ Erreur Telegram: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Erreur envoi Telegram: {e}")
            return False
    
    async def notify_success(
        self, 
        listing_title: str, 
        platform: str,
        url: Optional[str] = None
    ):
        """Notifier d'un postage réussi."""
        message = f"✅ <b>Annonce publiée avec succès !</b>\n\n"
        message += f"📦 <b>Titre:</b> {listing_title}\n"
        message += f"🌐 <b>Plateforme:</b> {platform.capitalize()}\n"
        
        if url:
            message += f"🔗 <a href='{url}'>Voir l'annonce</a>"
        
        await self.send_message(message)
    
    async def notify_failure(
        self, 
        listing_title: str, 
        platform: str,
        error: str
    ):
        """Notifier d'un échec de postage."""
        message = f"❌ <b>Échec du postage</b>\n\n"
        message += f"📦 <b>Titre:</b> {listing_title}\n"
        message += f"🌐 <b>Plateforme:</b> {platform.capitalize()}\n"
        message += f"⚠️ <b>Erreur:</b> {error[:500]}"  # Limiter la longueur
        
        await self.send_message(message)
    
    async def notify_scheduled(
        self, 
        listing_title: str, 
        scheduled_time: str
    ):
        """Notifier d'une annonce planifiée."""
        message = f"⏰ <b>Annonce planifiée</b>\n\n"
        message += f"📦 <b>Titre:</b> {listing_title}\n"
        message += f"📅 <b>Publication prévue:</b> {scheduled_time}"
        
        await self.send_message(message)


# Instance singleton
telegram_service = TelegramService()
