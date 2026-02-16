# 🚀 Démarrage Rapide avec Docker

## Installation en 3 Étapes

### 1. Créer le fichier .env

```bash
# Copier le fichier d'exemple
cp env.example .env

# Éditer .env et configurer au minimum:
# - DJANGO_SECRET_KEY (générez-en une nouvelle)
# - DB_PASSWORD
```

### 2. Construire et Lancer

```bash
# Construire les images
docker-compose build

# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f
```

### 3. Initialiser

```bash
# Appliquer les migrations
docker-compose exec web python manage.py migrate

# Créer un superutilisateur
docker-compose exec web python manage.py createsuperuser
```

## Accès

- **Application**: http://localhost:8000/
- **Admin**: http://localhost:8000/manager/

## Commandes Utiles

```bash
# Arrêter
docker-compose down

# Redémarrer
docker-compose restart

# Voir les logs
docker-compose logs -f web

# Ouvrir un shell
docker-compose exec web bash
```

## Avec Makefile

```bash
make build          # Construire
make up            # Démarrer
make down          # Arrêter
make logs          # Logs
make shell         # Shell
make migrate       # Migrations
```

---

Pour plus de détails, voir [DOCKER.md](DOCKER.md)
