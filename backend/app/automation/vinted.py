"""
Automatisation pour Vinted.
"""

from typing import List, Dict, Any, Optional

from app.automation.base import BaseAutomation


class VintedAutomation(BaseAutomation):
    """Automatisation du postage sur Vinted."""
    
    BASE_URL = "https://www.vinted.fr"
    LOGIN_URL = "https://www.vinted.fr/member/login"
    SELL_URL = "https://www.vinted.fr/items/new"
    
    async def login(self, email: str, password: str) -> bool:
        """
        Se connecter à Vinted.
        
        Note: Vinted utilise souvent des captchas et de la détection de bots.
        Cette méthode peut nécessiter des ajustements fréquents.
        """
        try:
            await self.page.goto(self.BASE_URL)
            await self.random_delay(2, 4)
            
            # Accepter les cookies si le bandeau apparaît
            try:
                cookie_button = await self.page.wait_for_selector(
                    '[data-testid="cookie-bar-accept-all"]',
                    timeout=5000
                )
                await cookie_button.click()
                await self.random_delay()
            except:
                pass  # Pas de bandeau de cookies
            
            # Cliquer sur "Se connecter"
            login_button = await self.page.wait_for_selector(
                '[data-testid="header--login-button"]',
                timeout=10000
            )
            await login_button.click()
            await self.random_delay(1, 2)
            
            # Attendre le formulaire de connexion
            await self.page.wait_for_selector('input[type="email"]', timeout=10000)
            
            # Remplir l'email
            await self.human_type('input[type="email"]', email)
            await self.random_delay()
            
            # Remplir le mot de passe
            await self.human_type('input[type="password"]', password)
            await self.random_delay()
            
            # Cliquer sur le bouton de connexion
            submit_button = await self.page.wait_for_selector(
                'button[type="submit"]',
                timeout=5000
            )
            await submit_button.click()
            
            # Attendre la redirection ou vérifier la connexion
            await self.random_delay(3, 5)
            
            # Vérifier si connecté (présence du menu utilisateur)
            try:
                await self.page.wait_for_selector(
                    '[data-testid="header--user-menu"]',
                    timeout=10000
                )
                return True
            except:
                await self.take_screenshot("vinted_login_failed")
                return False
                
        except Exception as e:
            await self.take_screenshot("vinted_login_error")
            raise Exception(f"Erreur de connexion Vinted: {str(e)}")
    
    async def post_listing(
        self,
        title: str,
        description: str,
        price: float,
        images: List[str],
        category: Optional[str] = None,
        brand: Optional[str] = None,
        condition: Optional[str] = None,
        size: Optional[str] = None,
        colors: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Poster une annonce sur Vinted.
        
        Args:
            title: Titre de l'annonce
            description: Description du produit
            price: Prix en euros
            images: Liste des chemins vers les images
            category: Catégorie Vinted
            brand: Marque
            condition: État (neuf, très bon état, etc.)
            size: Taille
            colors: Couleurs
        
        Returns:
            Dict avec success, url, et éventuellement error
        """
        try:
            # Aller sur la page de vente
            await self.page.goto(self.SELL_URL)
            await self.random_delay(2, 3)
            
            # Upload des images
            file_input = await self.page.wait_for_selector(
                'input[type="file"]',
                timeout=10000
            )
            
            for image_path in images:
                await file_input.set_input_files(image_path)
                await self.random_delay(1, 2)
            
            # Titre
            title_input = await self.page.wait_for_selector(
                '[data-testid="title-input"]',
                timeout=5000
            )
            await title_input.fill(title)
            await self.random_delay()
            
            # Description
            description_input = await self.page.wait_for_selector(
                '[data-testid="description-input"]',
                timeout=5000
            )
            await description_input.fill(description)
            await self.random_delay()
            
            # Catégorie (si spécifiée)
            if category:
                # La sélection de catégorie sur Vinted est complexe
                # Nécessite une navigation dans un arbre de catégories
                pass
            
            # Marque
            if brand:
                brand_input = await self.page.wait_for_selector(
                    '[data-testid="brand-input"]',
                    timeout=5000
                )
                await brand_input.fill(brand)
                await self.random_delay()
            
            # État
            if condition:
                # Sélectionner l'état du produit
                pass
            
            # Taille
            if size:
                size_input = await self.page.wait_for_selector(
                    '[data-testid="size-input"]',
                    timeout=5000
                )
                await size_input.fill(size)
                await self.random_delay()
            
            # Prix
            price_input = await self.page.wait_for_selector(
                '[data-testid="price-input"]',
                timeout=5000
            )
            await price_input.fill(str(price))
            await self.random_delay()
            
            # Soumettre
            submit_button = await self.page.wait_for_selector(
                '[data-testid="upload-submit-button"]',
                timeout=5000
            )
            await submit_button.click()
            
            # Attendre la confirmation
            await self.random_delay(3, 5)
            
            # Récupérer l'URL de l'annonce
            current_url = self.page.url
            
            if "/items/" in current_url:
                return {
                    "success": True,
                    "url": current_url,
                    "platform": "vinted"
                }
            else:
                await self.take_screenshot("vinted_post_unclear")
                return {
                    "success": False,
                    "error": "URL de confirmation non trouvée",
                    "platform": "vinted"
                }
                
        except Exception as e:
            await self.take_screenshot("vinted_post_error")
            return {
                "success": False,
                "error": str(e),
                "platform": "vinted"
            }
    
    async def delete_listing(self, listing_url: str) -> bool:
        """Supprimer une annonce Vinted."""
        try:
            await self.page.goto(listing_url)
            await self.random_delay(2, 3)
            
            # Cliquer sur le menu d'options
            options_button = await self.page.wait_for_selector(
                '[data-testid="item-actions-button"]',
                timeout=5000
            )
            await options_button.click()
            await self.random_delay()
            
            # Cliquer sur "Supprimer"
            delete_button = await self.page.wait_for_selector(
                '[data-testid="item-delete-button"]',
                timeout=5000
            )
            await delete_button.click()
            await self.random_delay()
            
            # Confirmer la suppression
            confirm_button = await self.page.wait_for_selector(
                '[data-testid="confirm-delete-button"]',
                timeout=5000
            )
            await confirm_button.click()
            
            await self.random_delay(2, 3)
            return True
            
        except Exception as e:
            await self.take_screenshot("vinted_delete_error")
            return False
