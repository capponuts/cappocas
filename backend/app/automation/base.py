"""
Classe de base pour l'automatisation avec Playwright.
"""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from fake_useragent import UserAgent

from app.core.config import settings


class BaseAutomation(ABC):
    """Classe de base pour l'automatisation des plateformes."""
    
    def __init__(self, proxy: Optional[str] = None):
        self.proxy = proxy
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.ua = UserAgent()
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def get_random_user_agent(self) -> str:
        """Obtenir un User-Agent aléatoire."""
        return self.ua.random
    
    def get_proxy_config(self) -> Optional[Dict[str, str]]:
        """Configurer le proxy si disponible."""
        if not self.proxy:
            return None
        
        # Format attendu: http://user:pass@ip:port ou http://ip:port
        return {"server": self.proxy}
    
    async def random_delay(self, min_sec: Optional[float] = None, max_sec: Optional[float] = None):
        """Attendre un délai aléatoire pour simuler un comportement humain."""
        min_delay = min_sec or settings.MIN_DELAY_BETWEEN_ACTIONS
        max_delay = max_sec or settings.MAX_DELAY_BETWEEN_ACTIONS
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def human_type(self, selector: str, text: str, delay_per_char: float = 0.05):
        """Taper du texte comme un humain (caractère par caractère)."""
        element = await self.page.wait_for_selector(selector)
        await element.click()
        
        for char in text:
            await self.page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.02, delay_per_char * 2))
    
    async def start(self):
        """Démarrer le navigateur."""
        playwright = await async_playwright().start()
        
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ]
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=browser_args,
        )
        
        context_options = {
            "user_agent": self.get_random_user_agent(),
            "viewport": {"width": 1920, "height": 1080},
            "locale": "fr-FR",
            "timezone_id": "Europe/Paris",
        }
        
        if self.proxy:
            context_options["proxy"] = self.get_proxy_config()
        
        self.context = await self.browser.new_context(**context_options)
        
        # Masquer les traces d'automatisation
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        self.page = await self.context.new_page()
    
    async def close(self):
        """Fermer le navigateur."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def take_screenshot(self, name: str) -> str:
        """Prendre une capture d'écran pour le debug."""
        screenshots_dir = Path("/app/screenshots")
        screenshots_dir.mkdir(exist_ok=True)
        
        path = screenshots_dir / f"{name}.png"
        await self.page.screenshot(path=str(path))
        return str(path)
    
    async def save_cookies(self) -> List[Dict[str, Any]]:
        """Sauvegarder les cookies de session."""
        return await self.context.cookies()
    
    async def load_cookies(self, cookies: List[Dict[str, Any]]):
        """Charger des cookies de session."""
        await self.context.add_cookies(cookies)
    
    @abstractmethod
    async def login(self, email: str, password: str) -> bool:
        """Se connecter à la plateforme."""
        pass
    
    @abstractmethod
    async def post_listing(
        self,
        title: str,
        description: str,
        price: float,
        images: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Poster une annonce."""
        pass
    
    @abstractmethod
    async def delete_listing(self, listing_url: str) -> bool:
        """Supprimer une annonce."""
        pass
