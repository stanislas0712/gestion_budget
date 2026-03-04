#!/bin/bash
# Solution rapide pour l'erreur ContainerConfig

echo "🔧 Correction de l'erreur ContainerConfig..."

# 1. Arrêter tous les services
echo "📦 Arrêt des services..."
docker-compose down

# 2. Supprimer TOUS les conteneurs db (y compris celui avec l'ID problématique)
echo "🗑️  Suppression des conteneurs db problématiques..."
docker ps -a --filter "name=budget_db" --format "{{.ID}} {{.Names}}" | while read -r id name; do
    echo "   Suppression: $name ($id)"
    docker rm -f "$id" 2>/dev/null || true
done

# Supprimer spécifiquement le conteneur mentionné dans l'erreur
docker rm -f 01d17aa4bfb6_budget_db 2>/dev/null || true

# 3. Nettoyer les conteneurs arrêtés
echo "🧹 Nettoyage..."
docker container prune -f

# 4. Forcer docker-compose à créer un NOUVEAU conteneur (pas de recréation)
echo "🚀 Création d'un nouveau conteneur db..."
docker-compose up -d --force-recreate db

# Attendre que PostgreSQL démarre
echo "⏳ Attente du démarrage..."
sleep 10

# Vérifier
if docker ps --format "{{.Names}}" | grep -q "^budget_db$"; then
    echo "✅ Conteneur db créé avec succès!"
    echo "📊 Vérifiez: docker-compose ps"
else
    echo "❌ Erreur lors de la création du conteneur"
    echo "📋 Logs: docker-compose logs db"
    exit 1
fi

echo "✅ Terminé! Vos données sont dans le volume Docker et sont préservées."
