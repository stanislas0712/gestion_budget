# 🐳 Guide Docker - Plateforme Budget

Ce guide explique comment lancer l'application avec Docker et Docker Compose.

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Installation Rapide](#installation-rapide)
3. [Architecture Docker](#architecture-docker)
4. [Configuration](#configuration)
5. [Commandes Utiles](#commandes-utiles)
6. [Dépannage](#dépannage)

---

## 🔧 Prérequis

- **Docker**: Version 20.10 ou supérieure
- **Docker Compose**: Version 2.0 ou supérieure

### Vérification

```bash
docker --version
docker-compose --version
```

---

## 🚀 Installation Rapide

### Étape 1: Cloner et Configurer

```bash
cd D:\Documents\luxdev\code\budget
```

### Étape 2: Créer le Fichier .env

Copiez le fichier d'exemple et modifiez les valeurs :

```bash
# Sur Windows PowerShell
Copy-Item env.example .env

# Sur Linux/Mac
cp env.example .env
```

Éditez `.env` et configurez :
- `DJANGO_SECRET_KEY` : Générez une clé secrète
- `DB_PASSWORD` : Mot de passe PostgreSQL
- `EMAIL_HOST_USER` et `EMAIL_HOST_PASSWORD` : Identifiants Gmail
- Autres variables selon vos besoins

### Étape 3: Construire et Lancer

```bash
# Construire les images
docker-compose build

# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f
```

### Étape 4: Initialiser la Base de Données

```bash
# Appliquer les migrations
docker-compose exec web python manage.py migrate

# Créer un superutilisateur
docker-compose exec web python manage.py createsuperuser
```

### Étape 5: Accéder à l'Application

- **Application**: http://localhost:8000/
- **Admin Django**: http://localhost:8000/manager/

---

## 🏗️ Architecture Docker

### Services Docker Compose

Le fichier `docker-compose.yml` définit les services suivants :

1. **db** (PostgreSQL)
   - Base de données principale
   - Port: 5432
   - Volume persistant: `postgres_data`

2. **redis** (Redis)
   - Broker pour Celery
   - Cache Django
   - Port: 6379
   - Volume persistant: `redis_data`

3. **web** (Django + Gunicorn)
   - Application principale
   - Port: 8000
   - 4 workers Gunicorn
   - Volumes: code source, staticfiles, media

4. **celery_worker** (Celery Worker)
   - Traitement des tâches asynchrones
   - 4 workers parallèles

5. **celery_beat** (Celery Beat)
   - Planification des tâches périodiques

6. **nginx** (Nginx - Production uniquement)
   - Reverse proxy
   - Servir les fichiers statiques
   - Port: 80
   - Actif avec le profil `production`

### Dockerfile Multi-Stage

Le `Dockerfile` utilise une construction multi-stage pour optimiser la taille de l'image :

#### Stage 1: Builder
- Installation des dépendances de compilation
- Création d'un virtualenv
- Installation de toutes les dépendances Python

#### Stage 2: Runtime
- Image Python minimale
- Copie du virtualenv depuis le builder
- Dépendances système minimales
- Utilisateur non-root pour la sécurité

**Avantages**:
- Image finale plus petite (~200MB vs ~800MB)
- Pas de dépendances de compilation dans l'image finale
- Sécurité améliorée (utilisateur non-root)

---

## ⚙️ Configuration

### Variables d'Environnement

Le fichier `.env` contient toutes les variables nécessaires :

```env
# Django
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=votre-cle-secrete
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données
DB_NAME=budget
DB_USER=budget
DB_PASSWORD=votre-mot-de-passe
DB_HOST=db  # Nom du service Docker

# Redis
REDIS_HOST=redis  # Nom du service Docker

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Ports
WEB_PORT=8000
DB_PORT=5432
REDIS_PORT=6379
```

### Génération d'une Clé Secrète

```bash
docker-compose exec web python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🛠️ Commandes Utiles

### Avec Makefile (Recommandé)

Si vous avez `make` installé :

```bash
make help          # Afficher toutes les commandes
make build         # Construire les images
make up            # Démarrer les services
make down          # Arrêter les services
make logs          # Voir les logs
make shell         # Ouvrir un shell dans le conteneur
make migrate       # Appliquer les migrations
make createsuperuser  # Créer un superutilisateur
```

### Avec Docker Compose

```bash
# Démarrer
docker-compose up -d

# Arrêter
docker-compose down

# Voir les logs
docker-compose logs -f web

# Exécuter une commande
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Redémarrer un service
docker-compose restart web

# Voir le statut
docker-compose ps
```

### Commandes Django dans le Conteneur

```bash
# Ouvrir un shell Django
docker-compose exec web python manage.py shell

# Créer des migrations
docker-compose exec web python manage.py makemigrations

# Appliquer les migrations
docker-compose exec web python manage.py migrate

# Collecter les fichiers statiques
docker-compose exec web python manage.py collectstatic --noinput

# Créer un utilisateur
docker-compose exec web python manage.py createsuperuser
```

### Commandes de Base de Données

```bash
# Se connecter à PostgreSQL
docker-compose exec db psql -U budget -d budget

# Backup de la base de données
docker-compose exec db pg_dump -U budget budget > backup.sql

# Restaurer une base de données
docker-compose exec -T db psql -U budget budget < backup.sql
```

---

## 🔍 Dépannage

### Problème: Les conteneurs ne démarrent pas

**Solution:**
```bash
# Voir les logs d'erreur
docker-compose logs

# Vérifier le statut
docker-compose ps

# Reconstruire les images
docker-compose build --no-cache
docker-compose up -d
```

### Problème: Erreur de connexion à la base de données

**Solution:**
```bash
# Vérifier que PostgreSQL est prêt
docker-compose exec db pg_isready -U budget

# Vérifier les logs de la base
docker-compose logs db

# Redémarrer la base de données
docker-compose restart db
```

### Problème: Les migrations ne s'appliquent pas

**Solution:**
```bash
# Forcer l'application des migrations
docker-compose exec web python manage.py migrate --run-syncdb

# Voir l'état des migrations
docker-compose exec web python manage.py showmigrations
```

### Problème: Les fichiers statiques ne se chargent pas

**Solution:**
```bash
# Collecter les fichiers statiques
docker-compose exec web python manage.py collectstatic --noinput

# Vérifier les permissions
docker-compose exec web ls -la /app/staticfiles
```

### Problème: Celery ne fonctionne pas

**Solution:**
```bash
# Vérifier les logs Celery
docker-compose logs celery_worker

# Redémarrer Celery
docker-compose restart celery_worker celery_beat

# Vérifier la connexion Redis
docker-compose exec redis redis-cli ping
```

### Problème: Port déjà utilisé

**Solution:**
Modifiez les ports dans `.env` :
```env
WEB_PORT=8001
DB_PORT=5433
REDIS_PORT=6380
```

### Problème: Permissions sur les volumes

**Solution:**
```bash
# Sur Linux/Mac, ajuster les permissions
sudo chown -R $USER:$USER .

# Vérifier les permissions dans le conteneur
docker-compose exec web ls -la /app
```

### Nettoyage Complet

```bash
# Arrêter et supprimer tout
docker-compose down -v

# Supprimer les images
docker-compose down --rmi all

# Nettoyer le système Docker
docker system prune -a --volumes
```

---

## 🚀 Déploiement en Production

### Mode Production avec Nginx

```bash
# Démarrer avec le profil production
docker-compose --profile production up -d

# L'application sera accessible sur le port 80 via Nginx
```

### Configuration Production

1. Modifiez `.env` :
   ```env
   DJANGO_DEBUG=0
   DJANGO_SECRET_KEY=<clé-secrète-forte>
   DJANGO_ALLOWED_HOSTS=votre-domaine.com
   ```

2. Configurez Nginx (`nginx.conf`) avec votre domaine

3. Activez HTTPS avec Let's Encrypt (recommandé)

### Optimisations Production

- Augmentez le nombre de workers Gunicorn
- Configurez un cache Redis pour Django
- Activez la compression gzip dans Nginx
- Configurez les backups automatiques de la base de données

---

## 📊 Monitoring

### Vérifier l'État des Services

```bash
# Statut des conteneurs
docker-compose ps

# Utilisation des ressources
docker stats

# Logs en temps réel
docker-compose logs -f
```

### Health Checks

Les services ont des health checks configurés :
- **db**: `pg_isready`
- **redis**: `redis-cli ping`
- **web**: `curl http://localhost:8000/`

---

## 🔐 Sécurité

### Bonnes Pratiques

1. **Ne jamais commiter `.env`** dans Git
2. Utiliser des mots de passe forts
3. Changer `DJANGO_SECRET_KEY` en production
4. Limiter `ALLOWED_HOSTS`
5. Utiliser HTTPS en production
6. L'utilisateur dans le conteneur est non-root

### Variables Sensibles

Toutes les variables sensibles doivent être dans `.env` :
- Mots de passe
- Clés API
- Tokens d'authentification

---

## 📚 Ressources

- [Documentation Docker](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Django avec Docker](https://docs.djangoproject.com/en/stable/howto/deployment/docker/)

---

**Dernière mise à jour**: 2024
