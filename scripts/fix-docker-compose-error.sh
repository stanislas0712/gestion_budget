#!/bin/bash
# Script pour résoudre l'erreur ContainerConfig de docker-compose

echo "🔧 Résolution de l'erreur ContainerConfig..."

# 1. Arrêter tous les conteneurs
echo "📦 Arrêt des conteneurs..."
docker-compose down

# 2. Supprimer le conteneur problématique
echo "🗑️  Suppression du conteneur db..."
docker rm -f budget_db 2>/dev/null || true

# 3. Nettoyer les images orphelines
echo "🧹 Nettoyage des images..."
docker image prune -f

# 4. Supprimer et recréer le volume PostgreSQL (optionnel - ATTENTION: supprime les données)
read -p "⚠️  Voulez-vous supprimer le volume PostgreSQL? Cela supprimera toutes les données. (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Suppression du volume postgres_data..."
    docker volume rm budget_postgres_data 2>/dev/null || true
fi

# 5. Reconstruire et redémarrer
echo "🚀 Reconstruction et redémarrage..."
docker-compose up -d --build

echo "✅ Terminé! Vérifiez les logs avec: docker-compose logs -f db"
