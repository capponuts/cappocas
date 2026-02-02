"""
Automatisation pour Leboncoin.
"""

from typing import List, Dict, Any, Optional

from app.automation.base import BaseAutomation


class LeboncoinAutomation(BaseAutomation):
    """Automatisation du postage sur Leboncoin."""
    
    BASE_URL = "https://www.leboncoin.fr"
    LOGIN_URL = "https://www.leboncoin.fr/compte/identification"
    SELL_URL = "https://www.leboncoin.fr/deposer-une-annonce"
    
    async def login(self, email: str, password: str) -> bool:
        """
        Se connecter à Leboncoin.
        
        Note: Leboncoin a des protections anti-bot assez agressives.
        Peut nécessiter des captchas manuels dans certains cas.
        """
        try:
            await self.page.goto(self.LOGIN_URL)
            await self.random_delay(2, 4)
            
            # Accepter les cookies
            try:
                cookie_button = await self.page.wait_for_selector(
                    '#didomi-notice-agree-button',
                    timeout=5000
                )
                await cookie_button.click()
                await self.random_delay()
            except:
                pass
            
            # Attendre le formulaire
            await self.page.wait_for_selector(
                'input[name="email"]',
                timeout=10000
            )
            
            # Remplir l'email
            await self.human_type('input[name="email"]', email)
            await self.random_delay()
            
            # Remplir le mot de passe
            await self.human_type('input[name="password"]', password)
            await self.random_delay()
            
            # Cliquer sur connexion
            submit_button = await self.page.wait_for_selector(
                'button[type="submit"]',
                timeout=5000
            )
            await submit_button.click()
            
            # Attendre la redirection
            await self.random_delay(3, 5)
            
            # Vérifier si connecté
            try:
                # Leboncoin redirige vers la page d'accueil après connexion
                await self.page.wait_for_selector(
                    '[data-test-id="user-menu"]',
                    timeout=10000
                )
                return True
            except:
                # Vérifier s'il y a un captcha
                if "captcha" in self.page.url.lower():
                    await self.take_screenshot("leboncoin_captcha")
                    raise Exception("Captcha détecté - intervention manuelle requise")
                
                await self.take_screenshot("leboncoin_login_failed")
                return False
                
        except Exception as e:
            await self.take_screenshot("leboncoin_login_error")
            raise Exception(f"Erreur de connexion Leboncoin: {str(e)}")
    
    async def post_listing(
        self,
        title: str,
        description: str,
        price: float,
        images: List[str],
        category: Optional[str] = None,
        location: Optional[str] = None,
        condition: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Poster une annonce sur Leboncoin.
        
        Args:
            title: Titre de l'annonce
            description: Description du produit
            price: Prix en euros
            images: Liste des chemins vers les images
            category: Catégorie Leboncoin
            location: Localisation
            condition: État du produit
        
        Returns:
            Dict avec success, url, et éventuellement error
        """
        try:
            # Aller sur la page de dépôt
            await self.page.goto(self.SELL_URL)
            await self.random_delay(2, 3)
            
            # Sélectionner la catégorie si spécifiée
            if category:
                # La sélection de catégorie sur Leboncoin nécessite
                # plusieurs clics dans une arborescence
                category_button = await self.page.wait_for_selector(
                    '[data-test-id="category-selector"]',
                    timeout=10000
                )
                await category_button.click()
                await self.random_delay()
                
                # Sélectionner la catégorie (simplifié)
                # En réalité, il faut naviguer dans l'arborescence
            
            # Upload des images
            file_input = await self.page.wait_for_selector(
                'input[type="file"][accept*="image"]',
                timeout=10000
            )
            
            for image_path in images:
                await file_input.set_input_files(image_path)
                await self.random_delay(1, 2)
            
            # Attendre que les images soient uploadées
            await self.random_delay(2, 4)
            
            # Titre
            title_input = await self.page.wait_for_selector(
                'input[name="subject"]',
                timeout=5000
            )
            await title_input.fill("")  # Clear
            await self.human_type('input[name="subject"]', title)
            await self.random_delay()
            
            # Description
            description_input = await self.page.wait_for_selector(
                'textarea[name="body"]',
                timeout=5000
            )
            await description_input.fill(description)
            await self.random_delay()
            
            # Prix
            price_input = await self.page.wait_for_selector(
                'input[name="price"]',
                timeout=5000
            )
            await price_input.fill(str(int(price)))
            await self.random_delay()
            
            # État du produit
            if condition:
                condition_select = await self.page.wait_for_selector(
                    '[data-test-id="condition-selector"]',
                    timeout=5000
                )
                await condition_select.click()
                await self.random_delay()
                # Sélectionner l'état approprié
            
            # Localisation
            if location:
                location_input = await self.page.wait_for_selector(
                    'input[name="location"]',
                    timeout=5000
                )
                await location_input.fill(location)
                await self.random_delay()
                
                # Sélectionner la première suggestion
                try:
                    suggestion = await self.page.wait_for_selector(
                        '[data-test-id="location-suggestion"]',
                        timeout=3000
                    )
                    await suggestion.click()
                except:
                    pass
            
            # Soumettre l'annonce
            submit_button = await self.page.wait_for_selector(
                'button[type="submit"]',
                timeout=5000
            )
            await submit_button.click()
            
            # Attendre la confirmation
            await self.random_delay(5, 8)
            
            # Vérifier le succès
            current_url = self.page.url
            
            # Leboncoin redirige vers la page de l'annonce après publication
            if "/offres/" in current_url or "/annonces/" in current_url:
                return {
                    "success": True,
                    "url": current_url,
                    "platform": "leboncoin"
                }
            
            # Vérifier s'il y a une page de confirmation
            try:
                success_message = await self.page.wait_for_selector(
                    '[data-test-id="success-message"]',
                    timeout=5000
                )
                
                # Récupérer le lien de l'annonce
                ad_link = await self.page.wait_for_selector(
                    'a[href*="/offres/"]',
                    timeout=5000
                )
                ad_url = await ad_link.get_attribute("href")
                
                return {
                    "success": True,
                    "url": ad_url,
                    "platform": "leboncoin"
                }
            except:
                await self.take_screenshot("leboncoin_post_unclear")
                return {
                    "success": False,
                    "error": "Impossible de confirmer la publication",
                    "platform": "leboncoin"
                }
                
        except Exception as e:
            await self.take_screenshot("leboncoin_post_error")
            return {
                "success": False,
                "error": str(e),
                "platform": "leboncoin"
            }
    
    async def delete_listing(self, listing_url: str) -> bool:
        """Supprimer une annonce Leboncoin."""
        try:
            await self.page.goto(listing_url)
            await self.random_delay(2, 3)
            
            # Cliquer sur le menu d'options
            options_button = await self.page.wait_for_selector(
                '[data-test-id="ad-options-button"]',
                timeout=5000
            )
            await options_button.click()
            await self.random_delay()
            
            # Cliquer sur "Supprimer"
            delete_button = await self.page.wait_for_selector(
                '[data-test-id="delete-ad-button"]',
                timeout=5000
            )
            await delete_button.click()
            await self.random_delay()
            
            # Confirmer la suppression
            confirm_button = await self.page.wait_for_selector(
                '[data-test-id="confirm-delete-button"]',
                timeout=5000
            )
            await confirm_button.click()
            
            await self.random_delay(2, 3)
            return True
            
        except Exception as e:
            await self.take_screenshot("leboncoin_delete_error")
            return False
