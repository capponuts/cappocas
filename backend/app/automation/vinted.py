"""
Automatisation pour Vinted avec sélection intelligente de catégories.
"""

from typing import List, Dict, Any, Optional

from app.automation.base import BaseAutomation
from app.services.category_service import category_service, VintedCategory


class VintedAutomation(BaseAutomation):
    """Automatisation du postage sur Vinted."""
    
    BASE_URL = "https://www.vinted.fr"
    LOGIN_URL = "https://www.vinted.fr/member/login"
    SELL_URL = "https://www.vinted.fr/items/new"
    
    # Mapping des états français vers les sélecteurs Vinted
    CONDITION_MAP = {
        "neuf": "Neuf avec étiquette",
        "neuf avec etiquette": "Neuf avec étiquette",
        "neuf sans etiquette": "Neuf sans étiquette",
        "très bon état": "Très bon état",
        "tres bon etat": "Très bon état",
        "bon état": "Bon état",
        "bon etat": "Bon état",
        "satisfaisant": "Satisfaisant",
    }
    
    async def is_logged_in(self) -> bool:
        """Vérifie si l'utilisateur est connecté."""
        try:
            # Vérifier la présence d'éléments uniquement visibles connectés
            # Le menu utilisateur (avatar), l'icône de profil, ou le lien vers le profil
            # Sur la capture réussie, on voit l'avatar en haut à droite
            await self.page.wait_for_selector(
                '[data-testid="header--user-menu"], '
                '[data-testid="header--user-profile-icon"], '
                '.user-profile-icon, '
                'a[href^="/member/"], '
                '[aria-label="Profil"]',
                timeout=5000
            )
            return True
        except:
            return False

    async def login(self, email: str, password: str, cookies: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Se connecter à Vinted.
        
        Note: Vinted utilise souvent des captchas et de la détection de bots.
        Cette méthode peut nécessiter des ajustements fréquents.
        """
        try:
            # Désactivation temporaire des cookies - on force le login classique
            # car les cookies expiraient et causaient des déconnexions
            print("🔑 Login classique par email/mot de passe (cookies désactivés)")
            
            # Utiliser l'URL de signup/select_type comme point d'entrée fiable
            # Augmentation du timeout pour le tunnel SSH qui peut être lent
            try:
                await self.page.goto(
                    "https://www.vinted.fr/member/signup/select_type?ref_url=%2F", 
                    timeout=60000, 
                    wait_until='domcontentloaded'
                )
                await self.page.wait_for_load_state('networkidle', timeout=30000)
            except Exception as e:
                print(f"⚠️ Page longue à charger: {e}")
            
            await self.random_delay(2, 4)
            
            # Accepter les cookies si le bandeau apparaît
            try:
                cookie_button = await self.page.wait_for_selector(
                    '[data-testid="cookie-bar-accept-all"], #onetrust-accept-btn-handler',
                    timeout=5000
                )
                await cookie_button.click()
                await self.random_delay()
            except:
                pass

            # 1. Cliquer sur "Se connecter" (le lien en bas "Tu as déjà un compte ? Se connecter")
            print("Tentative de clic sur 'Se connecter'...")
            try:
                # Utilisation de sélecteurs de texte pour être plus robuste
                await self.page.click('text="Se connecter"')
                await self.random_delay(1, 2)
                print("Clic sur 'Se connecter' réussi")
            except Exception as e:
                print(f"Échec clic 'Se connecter': {e}")
                # Fallback: essayer de trouver le lien par href si le texte échoue
                try:
                    await self.page.click('a[href*="login"]')
                    await self.random_delay(1, 2)
                except:
                    pass

            # 2. Cliquer sur "ou connecte-toi avec e-mail"
            print("Recherche de l'option email...")
            try:
                # Chercher le bouton/lien pour l'email
                # Les variantes de texte possibles
                email_selectors = [
                    'text="connecte-toi avec e-mail"',
                    'text="connecte-toi avec ton e-mail"',
                    'text="e-mail"',
                    '[data-testid="auth-select-type--email"]',
                    'span:has-text("e-mail")'
                ]
                
                for selector in email_selectors:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=2000)
                        if element and await element.is_visible():
                            await element.click()
                            await self.random_delay(1, 2)
                            print(f"Option email trouvée avec: {selector}")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Erreur sélection option email: {e}")

            # 3. Attendre le formulaire de connexion
            print("Attente du formulaire...")
            # Un champ username ou email doit apparaître
            await self.page.wait_for_selector('input[name="username"], input[name="email"], #username', timeout=10000)
            
            # Remplir l'email
            await self.human_type('input[name="username"], input[name="email"], #username', email)
            await self.random_delay()
            
            # Remplir le mot de passe
            await self.human_type('input[type="password"], input[name="password"]', password)
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
                    '[data-testid="header--user-menu"], [data-testid="header--avatar"]',
                    timeout=10000
                )
                return True
            except:
                await self.take_screenshot("vinted_login_failed")
                return False
                
        except Exception as e:
            await self.take_screenshot("vinted_login_error")
            raise Exception(f"Erreur de connexion Vinted: {str(e)}")
    
    async def _select_category(self, category: VintedCategory) -> bool:
        """
        Navigue dans l'arbre de catégories Vinted pour sélectionner la bonne catégorie.
        
        Args:
            category: La catégorie Vinted à sélectionner
        
        Returns:
            True si la sélection a réussi
        """
        try:
            # Cliquer sur le champ de catégorie pour ouvrir le sélecteur
            category_selector = await self.page.wait_for_selector(
                '[data-testid="category-select"], [data-testid="catalog-input"], '
                'button:has-text("Catégorie"), div[class*="catalog"]',
                timeout=5000
            )
            await category_selector.click()
            await self.random_delay(0.5, 1)
            
            # Naviguer dans chaque niveau de l'arbre de catégories
            for i, path_part in enumerate(category.path):
                # Attendre que le niveau actuel soit chargé
                await self.random_delay(0.3, 0.6)
                
                # Chercher et cliquer sur l'élément correspondant
                # Essayer plusieurs sélecteurs possibles
                selectors = [
                    f'li:has-text("{path_part}")',
                    f'button:has-text("{path_part}")',
                    f'a:has-text("{path_part}")',
                    f'div[role="option"]:has-text("{path_part}")',
                    f'span:has-text("{path_part}")',
                ]
                
                clicked = False
                for selector in selectors:
                    try:
                        element = await self.page.wait_for_selector(
                            selector,
                            timeout=3000
                        )
                        if element:
                            await element.click()
                            clicked = True
                            await self.random_delay(0.3, 0.5)
                            break
                    except:
                        continue
                
                if not clicked:
                    # Essayer avec une recherche textuelle
                    try:
                        await self.page.click(f'text="{path_part}"')
                        clicked = True
                        await self.random_delay(0.3, 0.5)
                    except:
                        pass
                
                if not clicked:
                    print(f"Impossible de cliquer sur: {path_part}")
                    await self.take_screenshot(f"vinted_category_error_{i}")
                    return False
            
            return True
            
        except Exception as e:
            await self.take_screenshot("vinted_category_selection_error")
            print(f"Erreur sélection catégorie: {e}")
            return False
    
    async def _select_condition(self, condition: str) -> bool:
        """
        Sélectionne l'état du produit.
        
        Args:
            condition: L'état (neuf, très bon état, etc.)
        
        Returns:
            True si la sélection a réussi
        """
        try:
            # Normaliser l'état
            condition_lower = condition.lower().strip()
            vinted_condition = self.CONDITION_MAP.get(
                condition_lower, 
                "Très bon état"  # Défaut
            )
            
            # Cliquer sur le sélecteur d'état
            condition_selector = await self.page.wait_for_selector(
                '[data-testid="status-select"], [data-testid="condition-input"], '
                'button:has-text("État"), div[class*="status"]',
                timeout=5000
            )
            await condition_selector.click()
            await self.random_delay(0.3, 0.6)
            
            # Sélectionner l'état
            selectors = [
                f'li:has-text("{vinted_condition}")',
                f'button:has-text("{vinted_condition}")',
                f'div[role="option"]:has-text("{vinted_condition}")',
            ]
            
            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.click()
                        return True
                except:
                    continue
            
            # Fallback: cliquer sur le texte directement
            try:
                await self.page.click(f'text="{vinted_condition}"')
                return True
            except:
                pass
            
            return False
            
        except Exception as e:
            print(f"Erreur sélection état: {e}")
            return False
    
    async def _select_brand(self, brand: str) -> bool:
        """
        Sélectionne ou saisit la marque.
        
        Args:
            brand: Nom de la marque
        
        Returns:
            True si la sélection a réussi
        """
        try:
            # Cliquer sur le champ marque
            brand_input = await self.page.wait_for_selector(
                '[data-testid="brand-input"], [data-testid="brand-select"], '
                'input[placeholder*="Marque"], input[placeholder*="marque"]',
                timeout=5000
            )
            await brand_input.click()
            await self.random_delay(0.3, 0.5)
            
            # Taper la marque
            await self.human_type(
                '[data-testid="brand-input"], [data-testid="brand-select"], '
                'input[placeholder*="Marque"], input[placeholder*="marque"]',
                brand
            )
            await self.random_delay(0.5, 1)
            
            # Attendre les suggestions et cliquer sur la première correspondance
            try:
                suggestion = await self.page.wait_for_selector(
                    f'li:has-text("{brand}"), div[role="option"]:has-text("{brand}")',
                    timeout=3000
                )
                if suggestion:
                    await suggestion.click()
                    return True
            except:
                # Pas de suggestion exacte, garder le texte saisi
                pass
            
            return True
            
        except Exception as e:
            print(f"Erreur sélection marque: {e}")
            return False
    
    async def _select_size(self, size: str, category: VintedCategory) -> bool:
        """
        Sélectionne la taille appropriée.
        
        Args:
            size: Taille (S, M, L, 38, etc.)
            category: Catégorie pour déterminer le type de taille
        
        Returns:
            True si la sélection a réussi
        """
        try:
            # Cliquer sur le sélecteur de taille
            size_selector = await self.page.wait_for_selector(
                '[data-testid="size-input"], [data-testid="size-select"], '
                'button:has-text("Taille"), div[class*="size"]',
                timeout=5000
            )
            await size_selector.click()
            await self.random_delay(0.3, 0.6)
            
            # Chercher et sélectionner la taille
            selectors = [
                f'li:has-text("{size}")',
                f'button:has-text("{size}")',
                f'div[role="option"]:has-text("{size}")',
            ]
            
            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.click()
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Erreur sélection taille: {e}")
            return False
    
    async def _select_colors(self, colors: List[str]) -> bool:
        """
        Sélectionne les couleurs.
        
        Args:
            colors: Liste des couleurs
        
        Returns:
            True si la sélection a réussi
        """
        try:
            # Cliquer sur le sélecteur de couleur
            color_selector = await self.page.wait_for_selector(
                '[data-testid="color-input"], [data-testid="color-select"], '
                'button:has-text("Couleur"), div[class*="color"]',
                timeout=5000
            )
            await color_selector.click()
            await self.random_delay(0.3, 0.6)
            
            # Sélectionner chaque couleur
            for color in colors[:2]:  # Vinted limite souvent à 2 couleurs
                try:
                    color_element = await self.page.wait_for_selector(
                        f'li:has-text("{color}"), button:has-text("{color}"), '
                        f'div[role="option"]:has-text("{color}")',
                        timeout=2000
                    )
                    if color_element:
                        await color_element.click()
                        await self.random_delay(0.2, 0.4)
                except:
                    continue
            
            # Fermer le sélecteur si nécessaire
            try:
                close_button = await self.page.wait_for_selector(
                    'button:has-text("Valider"), button:has-text("OK")',
                    timeout=1000
                )
                if close_button:
                    await close_button.click()
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"Erreur sélection couleurs: {e}")
            return False
    
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
        Poster une annonce sur Vinted avec catégorisation intelligente.
        
        Args:
            title: Titre de l'annonce
            description: Description du produit
            price: Prix en euros
            images: Liste des chemins vers les images
            category: Catégorie (optionnel, sera devinée si non fournie)
            brand: Marque
            condition: État (neuf, très bon état, etc.)
            size: Taille
            colors: Couleurs
        
        Returns:
            Dict avec success, url, et éventuellement error
        """
        try:
            # 1. Déterminer la catégorie automatiquement si non fournie
            detected_category = None
            if category:
                # Chercher la catégorie par nom/indice
                result = category_service.suggest_category(title, description, category)
                if result["category"]:
                    detected_category = result["category"]
            else:
                # Détecter automatiquement
                result = category_service.suggest_category(title, description)
                if result["category"]:
                    detected_category = result["category"]
                    print(f"Catégorie détectée: {' > '.join(detected_category.path)} "
                          f"(confiance: {result['confidence']:.0%})")
            
            if not detected_category:
                return {
                    "success": False,
                    "error": "Impossible de déterminer la catégorie automatiquement. "
                             "Veuillez spécifier une catégorie.",
                    "platform": "vinted"
                }
            
            # 2. Aller sur la page de vente
            await self.page.goto(self.SELL_URL)
            await self.random_delay(2, 3)
            
            # Accepter les cookies si nécessaire
            try:
                cookie_button = await self.page.wait_for_selector(
                    '[data-testid="cookie-bar-accept-all"], #onetrust-accept-btn-handler',
                    timeout=10000
                )
                await cookie_button.click()
                await self.random_delay()
            except:
                pass
            
            # 3. Upload des images
            print("📸 Début upload images...")
            try:
                # Attendre que l'input file soit dans le DOM (timeout long pour le tunnel)
                await self.page.wait_for_selector('input[type="file"]', state='attached', timeout=30000)
                
                # Forcer l'input à être visible et interactable via JS
                print("🔧 Forçage de la visibilité de l'input file...")
                await self.page.evaluate('''
                    () => {
                        const input = document.querySelector('input[type="file"]');
                        if (input) {
                            // Rendre l'input visible et utilisable
                            input.style.display = 'block';
                            input.style.visibility = 'visible';
                            input.style.opacity = '1';
                            input.style.position = 'relative';
                            input.style.width = '200px';
                            input.style.height = '50px';
                            input.style.zIndex = '9999';
                            // Retirer les attributs qui pourraient bloquer
                            input.removeAttribute('hidden');
                            input.removeAttribute('disabled');
                        }
                    }
                ''')
                
                await self.random_delay(1, 2)
                
                # Maintenant l'input est visible, on peut uploader
                file_input = await self.page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(images)
                    print(f"✅ Upload de {len(images)} image(s) réussi")
                else:
                    raise Exception("Input file introuvable après modification JS")
                    
            except Exception as e:
                await self.take_screenshot("vinted_upload_fail_debug")
                print(f"❌ Echec upload images: {e}")
                raise e
            
            print("📸 Images envoyées, attente traitement...")
            await self.random_delay(5, 8)  # Attendre le chargement et traitement
            
            # Vérifier si les images sont bien là (optionnel mais utile)
            # par ex chercher .item-photo-thumbnail ou similaire
            
            # 4. Titre
            title_input = await self.page.wait_for_selector(
                '[data-testid="title-input"], input[name="title"], '
                'input[placeholder*="titre"], input[placeholder*="Titre"]',
                timeout=30000
            )
            await title_input.fill(title)
            await self.random_delay()
            
            # 5. Description
            description_input = await self.page.wait_for_selector(
                '[data-testid="description-input"], textarea[name="description"], '
                'textarea[placeholder*="décris"], textarea[placeholder*="Décris"]',
                timeout=30000
            )
            await description_input.fill(description)
            await self.random_delay()
            
            # 6. Catégorie (navigation dans l'arbre)
            category_success = await self._select_category(detected_category)
            if not category_success:
                return {
                    "success": False,
                    "error": f"Impossible de sélectionner la catégorie: "
                             f"{' > '.join(detected_category.path)}",
                    "platform": "vinted",
                    "detected_category": detected_category.path
                }
            await self.random_delay()
            
            # 7. Marque (optionnel)
            if brand:
                await self._select_brand(brand)
                await self.random_delay()
            
            # 8. État
            if condition:
                await self._select_condition(condition)
                await self.random_delay()
            
            # 9. Taille (si applicable)
            if size and detected_category:
                await self._select_size(size, detected_category)
                await self.random_delay()
            
            # 10. Couleurs (optionnel)
            if colors:
                await self._select_colors(colors)
                await self.random_delay()
            
            # 11. Prix
            price_input = await self.page.wait_for_selector(
                '[data-testid="price-input"], input[name="price"], '
                'input[placeholder*="Prix"], input[placeholder*="prix"]',
                timeout=30000
            )
            await price_input.fill(str(int(price)))  # Vinted utilise des entiers
            await self.random_delay()
            
            # 12. Screenshot avant soumission (debug)
            await self.take_screenshot("vinted_before_submit")
            
            # 13. Soumettre
            print("🚀 Soumission formulaire...")
            submit_button = await self.page.wait_for_selector(
                '[data-testid="upload-submit-button"], '
                'button[type="submit"]:has-text("Ajouter"), '
                'button:has-text("Ajouter l\'article")',
                timeout=30000
            )
            await submit_button.click()
            
            # 14. Attendre la confirmation
            await self.random_delay(3, 5)
            
            # 15. Récupérer l'URL de l'annonce
            current_url = self.page.url
            
            if "/items/" in current_url:
                return {
                    "success": True,
                    "url": current_url,
                    "platform": "vinted",
                    "detected_category": detected_category.path
                }
            else:
                await self.take_screenshot("vinted_post_unclear")
                return {
                    "success": False,
                    "error": "URL de confirmation non trouvée. "
                             "L'annonce a peut-être été créée, vérifiez votre compte.",
                    "platform": "vinted",
                    "detected_category": detected_category.path
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
                '[data-testid="item-actions-button"], button[aria-label*="actions"], '
                'button:has-text("...")',
                timeout=5000
            )
            await options_button.click()
            await self.random_delay()
            
            # Cliquer sur "Supprimer"
            delete_button = await self.page.wait_for_selector(
                '[data-testid="item-delete-button"], button:has-text("Supprimer"), '
                'li:has-text("Supprimer")',
                timeout=5000
            )
            await delete_button.click()
            await self.random_delay()
            
            # Confirmer la suppression
            confirm_button = await self.page.wait_for_selector(
                '[data-testid="confirm-delete-button"], '
                'button:has-text("Confirmer"), button:has-text("Oui")',
                timeout=5000
            )
            await confirm_button.click()
            
            await self.random_delay(2, 3)
            return True
            
        except Exception as e:
            await self.take_screenshot("vinted_delete_error")
            return False
    
    async def analyze_listing(
        self,
        title: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Analyse un article et suggère les informations Vinted.
        Utile pour le frontend avant de poster.
        
        Args:
            title: Titre de l'annonce
            description: Description
        
        Returns:
            Dict avec catégorie suggérée, genre détecté, etc.
        """
        result = category_service.suggest_category(title, description)
        
        response = {
            "title": title,
            "description": description,
            "detected_gender": category_service.detect_gender(f"{title} {description}"),
        }
        
        if result["category"]:
            response.update({
                "suggested_category": {
                    "id": result["category"].id,
                    "name": result["category"].name,
                    "path": result["category"].path,
                    "full_path": " > ".join(result["category"].path),
                },
                "confidence": result["confidence"],
                "alternatives": [
                    {
                        "id": alt.id,
                        "name": alt.name,
                        "path": alt.path,
                        "full_path": " > ".join(alt.path),
                    }
                    for alt in result.get("alternatives", [])
                ]
            })
        else:
            response.update({
                "suggested_category": None,
                "confidence": 0,
                "message": result.get("message", "Aucune catégorie trouvée")
            })
        
        return response
