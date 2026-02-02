"""
Service de notification Discord via Webhook.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import httpx

from app.core.config import settings


class DiscordService:
    """Service pour envoyer des notifications via Discord Webhook."""
    
    # Couleurs pour les embeds Discord
    COLOR_SUCCESS = 0x22c55e  # Vert
    COLOR_ERROR = 0xef4444    # Rouge
    COLOR_WARNING = 0xf59e0b  # Orange
    COLOR_INFO = 0x6366f1     # Violet/Indigo
    
    def __init__(self):
        self.webhook_url = settings.DISCORD_WEBHOOK_URL
    
    @property
    def is_configured(self) -> bool:
        """Vérifier si le webhook est configuré."""
        return bool(self.webhook_url)
    
    async def send_message(
        self, 
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        username: str = "Cappocas Bot"
    ) -> bool:
        """
        Envoyer un message Discord via webhook.
        
        Args:
            content: Message texte simple (optionnel)
            embeds: Liste d'embeds formatés (optionnel)
            username: Nom du bot affiché
        
        Returns:
            bool: True si le message a été envoyé avec succès
        """
        if not self.is_configured:
            print("⚠️ Discord webhook non configuré")
            return False
        
        payload = {
            "username": username,
        }
        
        if content:
            payload["content"] = content
        
        if embeds:
            payload["embeds"] = embeds
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                
                # Discord retourne 204 No Content en cas de succès
                if response.status_code in [200, 204]:
                    return True
                else:
                    print(f"❌ Erreur Discord: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Erreur envoi Discord: {e}")
            return False
    
    def _create_embed(
        self,
        title: str,
        description: str,
        color: int,
        fields: Optional[List[Dict[str, Any]]] = None,
        url: Optional[str] = None,
        footer: Optional[str] = None,
        thumbnail_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Créer un embed Discord formaté."""
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if fields:
            embed["fields"] = fields
        
        if url:
            embed["url"] = url
        
        if footer:
            embed["footer"] = {"text": footer}
        
        if thumbnail_url:
            embed["thumbnail"] = {"url": thumbnail_url}
        
        return embed
    
    async def notify_success(
        self, 
        listing_title: str, 
        platform: str,
        url: Optional[str] = None
    ):
        """Notifier d'un postage réussi."""
        platform_emoji = "🟠" if platform.lower() == "leboncoin" else "🟢"
        
        fields = [
            {"name": "📦 Article", "value": listing_title, "inline": False},
            {"name": "🌐 Plateforme", "value": f"{platform_emoji} {platform.capitalize()}", "inline": True},
        ]
        
        if url:
            fields.append({"name": "🔗 Lien", "value": f"[Voir l'annonce]({url})", "inline": True})
        
        embed = self._create_embed(
            title="✅ Annonce publiée avec succès !",
            description="Votre annonce a été postée automatiquement.",
            color=self.COLOR_SUCCESS,
            fields=fields,
            url=url,
            footer="Cappocas - Automatisation d'annonces"
        )
        
        await self.send_message(embeds=[embed])
    
    async def notify_failure(
        self, 
        listing_title: str, 
        platform: str,
        error: str
    ):
        """Notifier d'un échec de postage."""
        platform_emoji = "🟠" if platform.lower() == "leboncoin" else "🟢"
        
        # Tronquer l'erreur si trop longue
        error_text = error[:500] + "..." if len(error) > 500 else error
        
        fields = [
            {"name": "📦 Article", "value": listing_title, "inline": False},
            {"name": "🌐 Plateforme", "value": f"{platform_emoji} {platform.capitalize()}", "inline": True},
            {"name": "⚠️ Erreur", "value": f"```{error_text}```", "inline": False},
        ]
        
        embed = self._create_embed(
            title="❌ Échec du postage",
            description="Une erreur s'est produite lors de la publication.",
            color=self.COLOR_ERROR,
            fields=fields,
            footer="Cappocas - Automatisation d'annonces"
        )
        
        await self.send_message(embeds=[embed])
    
    async def notify_scheduled(
        self, 
        listing_title: str, 
        scheduled_time: str
    ):
        """Notifier d'une annonce planifiée."""
        fields = [
            {"name": "📦 Article", "value": listing_title, "inline": False},
            {"name": "📅 Publication prévue", "value": scheduled_time, "inline": True},
        ]
        
        embed = self._create_embed(
            title="⏰ Annonce planifiée",
            description="Votre annonce sera publiée automatiquement.",
            color=self.COLOR_INFO,
            fields=fields,
            footer="Cappocas - Automatisation d'annonces"
        )
        
        await self.send_message(embeds=[embed])
    
    async def notify_login_success(self, platform: str):
        """Notifier d'une connexion réussie."""
        embed = self._create_embed(
            title="🔐 Connexion réussie",
            description=f"Connexion à **{platform.capitalize()}** établie avec succès.",
            color=self.COLOR_SUCCESS,
            footer="Cappocas - Automatisation d'annonces"
        )
        
        await self.send_message(embeds=[embed])
    
    async def notify_login_failure(self, platform: str, error: str):
        """Notifier d'un échec de connexion."""
        embed = self._create_embed(
            title="🔐 Échec de connexion",
            description=f"Impossible de se connecter à **{platform.capitalize()}**.",
            color=self.COLOR_ERROR,
            fields=[
                {"name": "Erreur", "value": f"```{error[:300]}```", "inline": False}
            ],
            footer="Cappocas - Automatisation d'annonces"
        )
        
        await self.send_message(embeds=[embed])
    
    async def notify_app_start(self):
        """Notifier du démarrage de l'application."""
        embed = self._create_embed(
            title="🚀 Cappocas démarré",
            description="L'application est prête à automatiser vos annonces !",
            color=self.COLOR_INFO,
            fields=[
                {"name": "Statut", "value": "✅ En ligne", "inline": True},
                {"name": "Version", "value": "1.0.0", "inline": True},
            ],
            footer="Cappocas - Automatisation d'annonces"
        )
        
        await self.send_message(embeds=[embed])
    
    async def send_log(
        self,
        level: str,
        message: str,
        details: Optional[str] = None
    ):
        """
        Envoyer un log à Discord.
        
        Args:
            level: Niveau du log (info, warning, error, success)
            message: Message principal
            details: Détails supplémentaires (optionnel)
        """
        colors = {
            "info": self.COLOR_INFO,
            "warning": self.COLOR_WARNING,
            "error": self.COLOR_ERROR,
            "success": self.COLOR_SUCCESS,
        }
        
        icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
        }
        
        color = colors.get(level.lower(), self.COLOR_INFO)
        icon = icons.get(level.lower(), "ℹ️")
        
        fields = []
        if details:
            fields.append({"name": "Détails", "value": f"```{details[:1000]}```", "inline": False})
        
        embed = self._create_embed(
            title=f"{icon} {level.upper()}",
            description=message,
            color=color,
            fields=fields if fields else None,
            footer="Cappocas Logs"
        )
        
        await self.send_message(embeds=[embed])


# Instance singleton
discord_service = DiscordService()
