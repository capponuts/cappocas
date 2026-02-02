"""
Service de catégorisation intelligente pour Vinted.
Analyse le titre et la description pour déterminer automatiquement la catégorie appropriée.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class VintedCategory:
    """Représente une catégorie Vinted avec son chemin complet."""
    id: int
    name: str
    path: List[str]  # Ex: ["Femmes", "Vêtements", "Hauts", "T-shirts"]
    keywords: List[str]  # Mots-clés pour identifier cette catégorie
    gender: Optional[str] = None  # "femme", "homme", "enfant", "mixte"


# Base de données des catégories Vinted avec mots-clés
# Structure: catégories principales avec leurs sous-catégories
VINTED_CATEGORIES: List[VintedCategory] = [
    # ==================== FEMMES - VÊTEMENTS ====================
    # Hauts
    VintedCategory(
        id=1,
        name="T-shirts",
        path=["Femmes", "Vêtements", "Hauts", "T-shirts"],
        keywords=["t-shirt", "tshirt", "tee-shirt", "tee shirt", "t shirt"],
        gender="femme"
    ),
    VintedCategory(
        id=2,
        name="Débardeurs",
        path=["Femmes", "Vêtements", "Hauts", "Débardeurs et tops sans manches"],
        keywords=["débardeur", "debardeur", "top sans manche", "top", "brassière", "crop top", "crop-top"],
        gender="femme"
    ),
    VintedCategory(
        id=3,
        name="Chemises et blouses",
        path=["Femmes", "Vêtements", "Hauts", "Chemises et blouses"],
        keywords=["chemise", "blouse", "chemisier", "tunique"],
        gender="femme"
    ),
    VintedCategory(
        id=4,
        name="Pulls et sweats",
        path=["Femmes", "Vêtements", "Hauts", "Pulls et sweats"],
        keywords=["pull", "sweat", "sweatshirt", "hoodie", "gilet", "cardigan", "tricot"],
        gender="femme"
    ),
    VintedCategory(
        id=5,
        name="Vestes et manteaux",
        path=["Femmes", "Vêtements", "Manteaux et vestes"],
        keywords=["veste", "manteau", "blouson", "parka", "doudoune", "trench", "blazer", "perfecto", "bombers", "bomber"],
        gender="femme"
    ),
    
    # Bas
    VintedCategory(
        id=10,
        name="Jeans",
        path=["Femmes", "Vêtements", "Bas", "Jeans"],
        keywords=["jean", "jeans", "denim"],
        gender="femme"
    ),
    VintedCategory(
        id=11,
        name="Pantalons",
        path=["Femmes", "Vêtements", "Bas", "Pantalons"],
        keywords=["pantalon", "pantacourt", "chino", "cargo", "jogger", "jogging"],
        gender="femme"
    ),
    VintedCategory(
        id=12,
        name="Shorts",
        path=["Femmes", "Vêtements", "Bas", "Shorts"],
        keywords=["short", "bermuda"],
        gender="femme"
    ),
    VintedCategory(
        id=13,
        name="Jupes",
        path=["Femmes", "Vêtements", "Bas", "Jupes"],
        keywords=["jupe", "mini-jupe", "minijupe"],
        gender="femme"
    ),
    
    # Robes
    VintedCategory(
        id=20,
        name="Robes",
        path=["Femmes", "Vêtements", "Robes"],
        keywords=["robe", "robe longue", "robe courte", "robe midi", "robe de soirée", "robe d'été"],
        gender="femme"
    ),
    VintedCategory(
        id=21,
        name="Combinaisons",
        path=["Femmes", "Vêtements", "Combinaisons et combishorts"],
        keywords=["combinaison", "combishort", "jumpsuit", "salopette"],
        gender="femme"
    ),
    
    # Chaussures femmes
    VintedCategory(
        id=30,
        name="Baskets",
        path=["Femmes", "Chaussures", "Baskets"],
        keywords=["basket", "baskets", "sneakers", "sneaker", "tennis"],
        gender="femme"
    ),
    VintedCategory(
        id=31,
        name="Escarpins",
        path=["Femmes", "Chaussures", "Escarpins"],
        keywords=["escarpin", "escarpins", "talon", "talons", "stiletto"],
        gender="femme"
    ),
    VintedCategory(
        id=32,
        name="Sandales",
        path=["Femmes", "Chaussures", "Sandales"],
        keywords=["sandale", "sandales", "tong", "tongs", "claquette", "claquettes", "mule", "mules"],
        gender="femme"
    ),
    VintedCategory(
        id=33,
        name="Bottes",
        path=["Femmes", "Chaussures", "Bottes"],
        keywords=["botte", "bottes", "bottine", "bottines", "boots", "cuissardes"],
        gender="femme"
    ),
    VintedCategory(
        id=34,
        name="Ballerines",
        path=["Femmes", "Chaussures", "Ballerines"],
        keywords=["ballerine", "ballerines"],
        gender="femme"
    ),
    VintedCategory(
        id=35,
        name="Mocassins",
        path=["Femmes", "Chaussures", "Mocassins et chaussures bateau"],
        keywords=["mocassin", "mocassins", "loafer", "loafers", "derbies", "derby"],
        gender="femme"
    ),
    
    # Sacs femmes
    VintedCategory(
        id=40,
        name="Sacs à main",
        path=["Femmes", "Sacs", "Sacs à main"],
        keywords=["sac à main", "sac a main", "sacoche", "cabas"],
        gender="femme"
    ),
    VintedCategory(
        id=41,
        name="Sacs bandoulière",
        path=["Femmes", "Sacs", "Sacs bandoulière"],
        keywords=["sac bandoulière", "sac bandouliere", "besace", "pochette"],
        gender="femme"
    ),
    VintedCategory(
        id=42,
        name="Sacs à dos",
        path=["Femmes", "Sacs", "Sacs à dos"],
        keywords=["sac à dos", "sac a dos", "backpack"],
        gender="femme"
    ),
    
    # Accessoires femmes
    VintedCategory(
        id=50,
        name="Bijoux",
        path=["Femmes", "Accessoires", "Bijoux"],
        keywords=["bijou", "bijoux", "collier", "bracelet", "bague", "boucle d'oreille", "boucles d'oreilles", "pendentif"],
        gender="femme"
    ),
    VintedCategory(
        id=51,
        name="Ceintures",
        path=["Femmes", "Accessoires", "Ceintures"],
        keywords=["ceinture"],
        gender="femme"
    ),
    VintedCategory(
        id=52,
        name="Écharpes et foulards",
        path=["Femmes", "Accessoires", "Écharpes, foulards et châles"],
        keywords=["écharpe", "echarpe", "foulard", "châle", "chale", "pashmina", "étole", "etole"],
        gender="femme"
    ),
    VintedCategory(
        id=53,
        name="Chapeaux et casquettes",
        path=["Femmes", "Accessoires", "Chapeaux et casquettes"],
        keywords=["chapeau", "casquette", "bonnet", "béret", "beret", "bob", "capeline"],
        gender="femme"
    ),
    VintedCategory(
        id=54,
        name="Lunettes de soleil",
        path=["Femmes", "Accessoires", "Lunettes de soleil"],
        keywords=["lunette", "lunettes", "soleil", "sunglasses"],
        gender="femme"
    ),
    VintedCategory(
        id=55,
        name="Montres",
        path=["Femmes", "Accessoires", "Montres"],
        keywords=["montre"],
        gender="femme"
    ),
    
    # ==================== HOMMES - VÊTEMENTS ====================
    # Hauts
    VintedCategory(
        id=100,
        name="T-shirts",
        path=["Hommes", "Vêtements", "Hauts", "T-shirts"],
        keywords=["t-shirt", "tshirt", "tee-shirt", "tee shirt", "t shirt"],
        gender="homme"
    ),
    VintedCategory(
        id=101,
        name="Chemises",
        path=["Hommes", "Vêtements", "Hauts", "Chemises"],
        keywords=["chemise", "chemisette"],
        gender="homme"
    ),
    VintedCategory(
        id=102,
        name="Pulls et sweats",
        path=["Hommes", "Vêtements", "Hauts", "Pulls et sweats"],
        keywords=["pull", "sweat", "sweatshirt", "hoodie", "gilet", "cardigan"],
        gender="homme"
    ),
    VintedCategory(
        id=103,
        name="Polos",
        path=["Hommes", "Vêtements", "Hauts", "Polos"],
        keywords=["polo"],
        gender="homme"
    ),
    VintedCategory(
        id=104,
        name="Vestes et manteaux",
        path=["Hommes", "Vêtements", "Manteaux et vestes"],
        keywords=["veste", "manteau", "blouson", "parka", "doudoune", "blazer", "perfecto", "bombers", "bomber"],
        gender="homme"
    ),
    
    # Bas hommes
    VintedCategory(
        id=110,
        name="Jeans",
        path=["Hommes", "Vêtements", "Bas", "Jeans"],
        keywords=["jean", "jeans", "denim"],
        gender="homme"
    ),
    VintedCategory(
        id=111,
        name="Pantalons",
        path=["Hommes", "Vêtements", "Bas", "Pantalons"],
        keywords=["pantalon", "chino", "cargo", "jogger", "jogging"],
        gender="homme"
    ),
    VintedCategory(
        id=112,
        name="Shorts",
        path=["Hommes", "Vêtements", "Bas", "Shorts"],
        keywords=["short", "bermuda"],
        gender="homme"
    ),
    
    # Chaussures hommes
    VintedCategory(
        id=120,
        name="Baskets",
        path=["Hommes", "Chaussures", "Baskets"],
        keywords=["basket", "baskets", "sneakers", "sneaker", "tennis"],
        gender="homme"
    ),
    VintedCategory(
        id=121,
        name="Chaussures de ville",
        path=["Hommes", "Chaussures", "Chaussures de ville"],
        keywords=["chaussure de ville", "richelieu", "derby", "oxford", "mocassin", "loafer"],
        gender="homme"
    ),
    VintedCategory(
        id=122,
        name="Bottes",
        path=["Hommes", "Chaussures", "Bottes"],
        keywords=["botte", "bottes", "bottine", "bottines", "boots", "chelsea"],
        gender="homme"
    ),
    VintedCategory(
        id=123,
        name="Sandales",
        path=["Hommes", "Chaussures", "Sandales"],
        keywords=["sandale", "sandales", "tong", "tongs", "claquette", "claquettes"],
        gender="homme"
    ),
    
    # Sacs hommes
    VintedCategory(
        id=130,
        name="Sacs à dos",
        path=["Hommes", "Sacs", "Sacs à dos"],
        keywords=["sac à dos", "sac a dos", "backpack"],
        gender="homme"
    ),
    VintedCategory(
        id=131,
        name="Sacoches",
        path=["Hommes", "Sacs", "Besaces et sacoches"],
        keywords=["sacoche", "besace", "messenger", "bandoulière", "bandouliere"],
        gender="homme"
    ),
    
    # Accessoires hommes
    VintedCategory(
        id=140,
        name="Ceintures",
        path=["Hommes", "Accessoires", "Ceintures"],
        keywords=["ceinture"],
        gender="homme"
    ),
    VintedCategory(
        id=141,
        name="Chapeaux et casquettes",
        path=["Hommes", "Accessoires", "Chapeaux et casquettes"],
        keywords=["chapeau", "casquette", "bonnet", "bob", "béret"],
        gender="homme"
    ),
    VintedCategory(
        id=142,
        name="Montres",
        path=["Hommes", "Accessoires", "Montres"],
        keywords=["montre"],
        gender="homme"
    ),
    VintedCategory(
        id=143,
        name="Lunettes de soleil",
        path=["Hommes", "Accessoires", "Lunettes de soleil"],
        keywords=["lunette", "lunettes", "soleil"],
        gender="homme"
    ),
    VintedCategory(
        id=144,
        name="Cravates et nœuds papillon",
        path=["Hommes", "Accessoires", "Cravates et nœuds papillon"],
        keywords=["cravate", "noeud papillon", "nœud papillon"],
        gender="homme"
    ),
    
    # ==================== ENFANTS ====================
    # Filles
    VintedCategory(
        id=200,
        name="Hauts fille",
        path=["Enfants", "Filles", "Vêtements", "Hauts"],
        keywords=["t-shirt", "pull", "sweat", "gilet", "chemise"],
        gender="enfant"
    ),
    VintedCategory(
        id=201,
        name="Robes fille",
        path=["Enfants", "Filles", "Vêtements", "Robes"],
        keywords=["robe"],
        gender="enfant"
    ),
    VintedCategory(
        id=202,
        name="Bas fille",
        path=["Enfants", "Filles", "Vêtements", "Bas"],
        keywords=["pantalon", "jean", "jupe", "short", "legging"],
        gender="enfant"
    ),
    
    # Garçons
    VintedCategory(
        id=210,
        name="Hauts garçon",
        path=["Enfants", "Garçons", "Vêtements", "Hauts"],
        keywords=["t-shirt", "pull", "sweat", "gilet", "chemise"],
        gender="enfant"
    ),
    VintedCategory(
        id=211,
        name="Bas garçon",
        path=["Enfants", "Garçons", "Vêtements", "Bas"],
        keywords=["pantalon", "jean", "short", "jogging"],
        gender="enfant"
    ),
    
    # ==================== MAISON ====================
    VintedCategory(
        id=300,
        name="Décoration",
        path=["Maison", "Décoration"],
        keywords=["déco", "deco", "décoration", "decoration", "cadre", "vase", "bougie", "coussin", "miroir", "tableau"],
        gender="mixte"
    ),
    VintedCategory(
        id=301,
        name="Vaisselle",
        path=["Maison", "Cuisine et salle à manger", "Vaisselle"],
        keywords=["assiette", "verre", "tasse", "mug", "bol", "vaisselle", "couverts"],
        gender="mixte"
    ),
    VintedCategory(
        id=302,
        name="Linge de maison",
        path=["Maison", "Linge de maison"],
        keywords=["drap", "housse", "couette", "oreiller", "serviette", "nappe", "rideau"],
        gender="mixte"
    ),
    
    # ==================== ÉLECTRONIQUE ====================
    VintedCategory(
        id=400,
        name="Smartphones",
        path=["Électronique", "Téléphones et accessoires", "Smartphones"],
        keywords=["téléphone", "telephone", "smartphone", "iphone", "samsung", "huawei", "xiaomi"],
        gender="mixte"
    ),
    VintedCategory(
        id=401,
        name="Tablettes",
        path=["Électronique", "Tablettes et liseuses"],
        keywords=["tablette", "ipad", "kindle", "liseuse"],
        gender="mixte"
    ),
    VintedCategory(
        id=402,
        name="Consoles de jeux",
        path=["Électronique", "Consoles et jeux vidéo", "Consoles"],
        keywords=["console", "playstation", "xbox", "nintendo", "switch", "ps4", "ps5"],
        gender="mixte"
    ),
    VintedCategory(
        id=403,
        name="Jeux vidéo",
        path=["Électronique", "Consoles et jeux vidéo", "Jeux"],
        keywords=["jeu vidéo", "jeux vidéo", "jeu video", "jeux video"],
        gender="mixte"
    ),
    VintedCategory(
        id=404,
        name="Écouteurs et casques",
        path=["Électronique", "Audio", "Écouteurs et casques"],
        keywords=["écouteur", "ecouteur", "casque", "airpods", "earbuds", "audio"],
        gender="mixte"
    ),
    
    # ==================== BEAUTÉ ====================
    VintedCategory(
        id=500,
        name="Maquillage",
        path=["Beauté", "Maquillage"],
        keywords=["maquillage", "rouge à lèvres", "mascara", "fond de teint", "eye-liner", "fard"],
        gender="femme"
    ),
    VintedCategory(
        id=501,
        name="Parfums",
        path=["Beauté", "Parfums"],
        keywords=["parfum", "eau de toilette", "eau de parfum", "cologne", "fragrance"],
        gender="mixte"
    ),
    VintedCategory(
        id=502,
        name="Soins",
        path=["Beauté", "Soins du visage et du corps"],
        keywords=["crème", "creme", "sérum", "serum", "soin", "lotion", "huile"],
        gender="mixte"
    ),
    
    # ==================== SPORT ====================
    VintedCategory(
        id=600,
        name="Vêtements de sport femme",
        path=["Sport", "Fitness et gym", "Vêtements de sport"],
        keywords=["legging sport", "brassière sport", "t-shirt sport", "short sport", "yoga", "fitness", "gym"],
        gender="femme"
    ),
    VintedCategory(
        id=601,
        name="Vêtements de sport homme",
        path=["Sport", "Fitness et gym", "Vêtements de sport"],
        keywords=["short sport", "t-shirt sport", "débardeur sport", "jogging sport"],
        gender="homme"
    ),
    VintedCategory(
        id=602,
        name="Chaussures de sport",
        path=["Sport", "Chaussures de sport"],
        keywords=["chaussure de sport", "running", "course", "trail", "football", "basket sport"],
        gender="mixte"
    ),
    VintedCategory(
        id=603,
        name="Équipement sportif",
        path=["Sport", "Équipement sportif"],
        keywords=["haltère", "tapis", "corde à sauter", "bande élastique", "ballon", "raquette"],
        gender="mixte"
    ),
]


# Mots-clés pour détecter le genre
GENDER_KEYWORDS = {
    "femme": [
        "femme", "femmes", "fille", "madame", "lady", "women", "woman",
        "féminin", "feminin", "pour elle", "taille 34", "taille 36", "taille 38",
        "taille 40", "taille 42", "taille 44", "taille xs", "taille s femme",
        "robe", "jupe", "escarpin", "ballerine", "soutien-gorge", "culotte"
    ],
    "homme": [
        "homme", "hommes", "garçon", "garcon", "monsieur", "men", "man",
        "masculin", "pour lui", "taille m homme", "taille l homme", "taille xl",
        "cravate", "costume homme"
    ],
    "enfant": [
        "enfant", "enfants", "bébé", "bebe", "baby", "kids", "junior",
        "fille", "garçon", "garcon", "ado", "adolescent",
        "taille 2 ans", "taille 3 ans", "taille 4 ans", "taille 5 ans",
        "taille 6 ans", "taille 8 ans", "taille 10 ans", "taille 12 ans", "taille 14 ans"
    ]
}


class CategoryService:
    """Service de catégorisation intelligente."""
    
    def __init__(self):
        self.categories = VINTED_CATEGORIES
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """Construit un index inversé des mots-clés."""
        self.keyword_index: Dict[str, List[VintedCategory]] = {}
        
        for category in self.categories:
            for keyword in category.keywords:
                keyword_lower = keyword.lower()
                if keyword_lower not in self.keyword_index:
                    self.keyword_index[keyword_lower] = []
                self.keyword_index[keyword_lower].append(category)
    
    def detect_gender(self, text: str) -> Optional[str]:
        """
        Détecte le genre cible à partir du texte.
        
        Returns:
            "femme", "homme", "enfant" ou None si indéterminé
        """
        text_lower = text.lower()
        
        scores = {"femme": 0, "homme": 0, "enfant": 0}
        
        for gender, keywords in GENDER_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[gender] += 1
        
        # Retourner le genre avec le score le plus élevé
        max_score = max(scores.values())
        if max_score == 0:
            return None
        
        for gender, score in scores.items():
            if score == max_score:
                return gender
        
        return None
    
    def find_category(
        self,
        title: str,
        description: str = "",
        user_hint: Optional[str] = None
    ) -> Tuple[Optional[VintedCategory], float]:
        """
        Trouve la meilleure catégorie Vinted basée sur le titre et la description.
        
        Args:
            title: Titre de l'annonce
            description: Description de l'annonce
            user_hint: Indice optionnel de l'utilisateur (ex: "femme", "homme", "chaussures")
        
        Returns:
            Tuple (catégorie trouvée, score de confiance 0-1)
        """
        text = f"{title} {description}".lower()
        
        # Détecter le genre
        detected_gender = self.detect_gender(text)
        if user_hint:
            # L'indice utilisateur a priorité
            if user_hint.lower() in ["femme", "femmes", "f"]:
                detected_gender = "femme"
            elif user_hint.lower() in ["homme", "hommes", "h", "m"]:
                detected_gender = "homme"
            elif user_hint.lower() in ["enfant", "enfants", "kid", "kids"]:
                detected_gender = "enfant"
        
        # Chercher les correspondances de mots-clés
        category_scores: Dict[int, float] = {}
        
        for category in self.categories:
            score = 0.0
            
            # Vérifier chaque mot-clé
            for keyword in category.keywords:
                keyword_lower = keyword.lower()
                
                # Correspondance exacte dans le titre (bonus x2)
                if keyword_lower in title.lower():
                    score += 2.0
                
                # Correspondance dans la description
                elif keyword_lower in text:
                    score += 1.0
            
            # Bonus si le genre correspond
            if detected_gender and category.gender:
                if category.gender == detected_gender:
                    score *= 1.5
                elif category.gender != "mixte" and detected_gender != category.gender:
                    score *= 0.3  # Pénalité si le genre ne correspond pas
            
            if score > 0:
                category_scores[category.id] = score
        
        if not category_scores:
            return None, 0.0
        
        # Trouver la meilleure catégorie
        best_id = max(category_scores, key=category_scores.get)
        best_score = category_scores[best_id]
        
        # Normaliser le score (0-1)
        max_possible_score = 10.0  # Score maximum théorique
        confidence = min(best_score / max_possible_score, 1.0)
        
        best_category = next(c for c in self.categories if c.id == best_id)
        
        return best_category, confidence
    
    def get_category_path(self, category: VintedCategory) -> List[str]:
        """Retourne le chemin complet de la catégorie."""
        return category.path
    
    def search_categories(self, query: str, limit: int = 5) -> List[VintedCategory]:
        """
        Recherche des catégories par mot-clé.
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats
        
        Returns:
            Liste des catégories correspondantes
        """
        query_lower = query.lower()
        results = []
        
        for category in self.categories:
            # Chercher dans le nom
            if query_lower in category.name.lower():
                results.append(category)
                continue
            
            # Chercher dans les mots-clés
            for keyword in category.keywords:
                if query_lower in keyword.lower():
                    results.append(category)
                    break
            
            # Chercher dans le chemin
            for path_part in category.path:
                if query_lower in path_part.lower():
                    results.append(category)
                    break
        
        return results[:limit]
    
    def get_all_categories(self) -> List[Dict]:
        """Retourne toutes les catégories formatées."""
        return [
            {
                "id": c.id,
                "name": c.name,
                "path": c.path,
                "full_path": " > ".join(c.path),
                "gender": c.gender
            }
            for c in self.categories
        ]
    
    def suggest_category(
        self,
        title: str,
        description: str = "",
        user_category: Optional[str] = None
    ) -> Dict:
        """
        Suggère une catégorie avec toutes les informations utiles.
        
        Returns:
            Dict avec:
            - category: la catégorie suggérée
            - confidence: score de confiance
            - path: chemin complet
            - alternatives: autres suggestions possibles
        """
        # Si l'utilisateur a donné un indice de catégorie
        if user_category:
            # D'abord chercher une correspondance exacte
            matches = self.search_categories(user_category, limit=3)
            if matches:
                return {
                    "category": matches[0],
                    "confidence": 0.9,
                    "path": matches[0].path,
                    "alternatives": matches[1:] if len(matches) > 1 else []
                }
        
        # Sinon, analyser le texte
        best_category, confidence = self.find_category(title, description, user_category)
        
        if not best_category:
            return {
                "category": None,
                "confidence": 0.0,
                "path": [],
                "alternatives": [],
                "message": "Impossible de déterminer la catégorie automatiquement"
            }
        
        # Chercher des alternatives
        text = f"{title} {description}"
        alternatives = []
        for cat in self.categories:
            if cat.id != best_category.id:
                _, score = self.find_category(title, description)
                if score > 0.3:
                    alternatives.append(cat)
        
        return {
            "category": best_category,
            "confidence": confidence,
            "path": best_category.path,
            "alternatives": alternatives[:3]
        }


# Instance singleton
category_service = CategoryService()
