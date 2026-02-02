# Cappocas - Automatisation d'annonces

Application web pour automatiser le postage d'annonces sur Leboncoin et Vinted.

**Production** : https://cappocas.capponuts.fr

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Traefik (Reverse Proxy + SSL)                 │
│              cappocas.capponuts.fr (Let's Encrypt)               │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│ Frontend  │  │  Backend  │  │  Flower   │
│ (Nginx)   │  │ (FastAPI) │  │ (Monitor) │
│   :80     │  │   :8000   │  │   :5555   │
└───────────┘  └─────┬─────┘  └───────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│  Celery   │  │PostgreSQL │  │   Redis   │
│  Worker   │  │   :5432   │  │   :6379   │
└─────┬─────┘  └───────────┘  └───────────┘
      │
      ▼
┌───────────┐  ┌───────────┐
│ Playwright│  │   MinIO   │
│ (Browser) │  │ (Storage) │
└───────────┘  └───────────┘
```

## Prérequis

- Docker & Docker Compose
- 8 Go RAM minimum (recommandé)
- Un compte Telegram avec un bot créé (optionnel)

## Installation rapide

### 1. Cloner et configurer

```bash
# Copier le fichier de configuration
cp .env.example .env

# Éditer les variables d'environnement
nano .env
```

### 2. Configuration minimale du .env

```env
# Credentials Leboncoin
LEBONCOIN_EMAIL=votre_email@example.com
LEBONCOIN_PASSWORD=votre_mot_de_passe

# Credentials Vinted
VINTED_EMAIL=votre_email@example.com
VINTED_PASSWORD=votre_mot_de_passe

# Telegram (optionnel mais recommandé)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789

# Sécurité - CHANGEZ CES VALEURS !
SECRET_KEY=une_cle_secrete_tres_longue_et_aleatoire
POSTGRES_PASSWORD=un_mot_de_passe_securise
```

### 3. Lancer l'application

```bash
# Build et démarrage
docker-compose up -d --build

# Voir les logs
docker-compose logs -f
```

### 4. Accéder à l'application

- **Interface web** : http://localhost
- **API** : http://localhost/api
- **Flower (monitoring)** : http://localhost:5555
- **MinIO Console** : http://localhost:9001

## Déploiement VPS (Hostinger)

L'application est déployée sur un VPS Hostinger avec Traefik comme reverse proxy.

### Configuration VPS

| Élément | Valeur |
|---------|--------|
| **URL** | https://cappocas.capponuts.fr |
| **Reverse Proxy** | Traefik (partagé avec n8n) |
| **SSL** | Let's Encrypt (auto-renouvelé) |
| **Répertoire** | `/docker/cappocas/` |

### Fichiers sur le VPS

```
/docker/
├── cappocas/
│   ├── docker-compose.yml    # Config Docker Compose
│   └── .env                  # Variables d'environnement
└── n8n/
    ├── docker-compose.yml    # Config n8n + Traefik
    └── dynamic/
        └── cappocas.yml      # Routes Traefik pour Cappocas
```

### Commandes de gestion sur le VPS

```bash
# Connexion SSH
ssh root@72.62.237.27

# Voir les logs
cd /docker/cappocas && docker compose logs -f

# Redémarrer les services
docker compose down && docker compose up -d

# Redémarrer Traefik après modification des routes
docker restart n8n-traefik-1
```

## Utilisation

### 1. Créer un compte

Accédez à l'interface web et créez un compte utilisateur.

### 2. Configurer vos comptes

Dans les paramètres, ajoutez vos identifiants Leboncoin et Vinted.

### 3. Créer une annonce

1. Cliquez sur "Nouvelle annonce"
2. Uploadez vos photos
3. Remplissez les informations (titre, description, prix)
4. Sélectionnez les plateformes cibles
5. Publiez ou planifiez la publication

### 4. Suivre les publications

- Le tableau de bord affiche le statut de vos annonces
- Les notifications Telegram vous informent des succès/échecs

## Configuration des proxies

Pour éviter les bans, configurez des proxies dans `backend/config/proxies.txt` :

```
http://user:pass@ip1:port
http://user:pass@ip2:port
http://user:pass@ip3:port
```

**Recommandation** : Utilisez des proxies résidentiels de qualité (Bright Data, Oxylabs, SmartProxy).

## Configuration Telegram

### 1. Créer un bot

1. Ouvrez Telegram et cherchez `@BotFather`
2. Envoyez `/newbot` et suivez les instructions
3. Récupérez le token du bot

### 2. Obtenir votre Chat ID

1. Cherchez `@userinfobot` sur Telegram
2. Démarrez une conversation
3. Récupérez votre Chat ID

### 3. Configurer dans .env

```env
TELEGRAM_BOT_TOKEN=votre_token
TELEGRAM_CHAT_ID=votre_chat_id
```

## Délais anti-ban

Les délais sont configurables dans `.env` :

```env
# Délai entre les posts (en secondes)
MIN_DELAY_BETWEEN_POSTS=300    # 5 minutes
MAX_DELAY_BETWEEN_POSTS=900    # 15 minutes

# Délai entre les actions (clic, typing, etc.)
MIN_DELAY_BETWEEN_ACTIONS=2
MAX_DELAY_BETWEEN_ACTIONS=5
```

## Commandes Docker utiles

```bash
# Arrêter tous les services
docker-compose down

# Voir les logs d'un service
docker-compose logs -f backend

# Redémarrer un service
docker-compose restart celery_worker

# Reconstruire après modifications
docker-compose up -d --build

# Nettoyer les volumes (ATTENTION: supprime les données)
docker-compose down -v
```

## Structure du projet

```
cappocas/
├── backend/
│   ├── app/
│   │   ├── api/            # Routes API
│   │   ├── automation/     # Playwright (Vinted, Leboncoin)
│   │   ├── core/           # Config, DB, Security
│   │   ├── models/         # Modèles SQLAlchemy
│   │   ├── services/       # Services (MinIO, Telegram)
│   │   └── tasks/          # Tâches Celery
│   ├── config/
│   │   └── proxies.txt     # Liste des proxies
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.js         # Application JS
│   │   └── styles.css      # Styles
│   ├── index.html
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── .env
└── README.md
```

## API Endpoints

### Authentification
- `POST /api/auth/register` - Créer un compte
- `POST /api/auth/login` - Se connecter
- `GET /api/auth/me` - Infos utilisateur

### Annonces
- `GET /api/listings/` - Liste des annonces
- `POST /api/listings/` - Créer une annonce
- `GET /api/listings/{id}` - Détail d'une annonce
- `PUT /api/listings/{id}` - Modifier une annonce
- `DELETE /api/listings/{id}` - Supprimer une annonce
- `POST /api/listings/{id}/publish` - Publier une annonce

### Uploads
- `POST /api/uploads/images` - Uploader des images
- `DELETE /api/uploads/images/{id}` - Supprimer une image

### Tâches
- `GET /api/tasks/{id}` - Statut d'une tâche
- `DELETE /api/tasks/{id}` - Annuler une tâche

## Limitations et avertissements

⚠️ **Avertissement légal** : L'automatisation de Leboncoin et Vinted viole leurs Conditions Générales d'Utilisation. Utilisez cette application à vos propres risques.

### Limitations connues

- Les captchas peuvent bloquer les connexions
- Les plateformes mettent régulièrement à jour leurs protections
- Les sélecteurs CSS peuvent changer et nécessiter des mises à jour

### Recommandations

1. **Utilisez des proxies résidentiels** de qualité
2. **Ne postez pas trop fréquemment** - respectez les délais anti-ban
3. **Variez les horaires** de publication
4. **Surveillez les notifications** Telegram pour détecter les problèmes

## Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs
docker-compose logs

# Vérifier que tous les conteneurs sont up
docker-compose ps
```

### Erreur de connexion aux plateformes

1. Vérifiez vos identifiants dans `.env`
2. Vérifiez les captures d'écran dans `/app/screenshots`
3. Un captcha peut être requis - connectez-vous manuellement d'abord

### Les images ne s'uploadent pas

1. Vérifiez que MinIO est accessible sur le port 9001
2. Vérifiez les credentials MinIO dans `.env`

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir des issues ou des pull requests.

## Licence

Ce projet est fourni à des fins éducatives uniquement.
