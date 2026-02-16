.PHONY: help build up down restart logs shell migrate createsuperuser collectstatic test clean

help: ## Affiche cette aide
	@echo "Commandes disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construire les images Docker
	docker-compose build

up: ## Démarrer tous les services
	docker-compose up -d

down: ## Arrêter tous les services
	docker-compose down

restart: ## Redémarrer tous les services
	docker-compose restart

logs: ## Afficher les logs de tous les services
	docker-compose logs -f

logs-web: ## Afficher les logs du service web
	docker-compose logs -f web

logs-db: ## Afficher les logs de la base de données
	docker-compose logs -f db

logs-celery: ## Afficher les logs de Celery
	docker-compose logs -f celery_worker celery_beat

shell: ## Ouvrir un shell dans le conteneur web
	docker-compose exec web bash

shell-db: ## Ouvrir un shell PostgreSQL
	docker-compose exec db psql -U budget -d budget

migrate: ## Appliquer les migrations
	docker-compose exec web python manage.py migrate

makemigrations: ## Créer de nouvelles migrations
	docker-compose exec web python manage.py makemigrations

createsuperuser: ## Créer un superutilisateur
	docker-compose exec web python manage.py createsuperuser

collectstatic: ## Collecter les fichiers statiques
	docker-compose exec web python manage.py collectstatic --noinput

test: ## Lancer les tests
	docker-compose exec web python manage.py test

clean: ## Nettoyer les conteneurs et volumes
	docker-compose down -v
	docker system prune -f

rebuild: ## Reconstruire et redémarrer
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

dev: ## Démarrer en mode développement (avec volumes)
	docker-compose up

prod: ## Démarrer en mode production (avec Nginx)
	docker-compose --profile production up -d

status: ## Afficher le statut des services
	docker-compose ps
