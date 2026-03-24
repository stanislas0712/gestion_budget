#!/bin/bash
# Script pour copier les templates depuis l'hôte vers le conteneur Docker

echo "📋 Copie des templates vers le conteneur Docker..."

# Vérifier que le fichier source existe
SOURCE_FILE="media/templates/template_budget.xlsx"
if [ ! -f "$SOURCE_FILE" ]; then
    echo "❌ Erreur: Le fichier $SOURCE_FILE n'existe pas"
    exit 1
fi

# Nom du conteneur
CONTAINER_NAME="budget_web"

# Vérifier que le conteneur est en cours d'exécution
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Erreur: Le conteneur $CONTAINER_NAME n'est pas en cours d'exécution"
    echo "💡 Démarrez le conteneur avec: docker-compose up -d"
    exit 1
fi

# Créer le dossier de destination dans le conteneur
docker exec $CONTAINER_NAME mkdir -p /app/media/templates

# Copier le fichier
echo "📁 Copie de $SOURCE_FILE vers le conteneur..."
docker cp "$SOURCE_FILE" "$CONTAINER_NAME:/app/media/templates/"

# Copier tous les autres fichiers du dossier templates
if [ -d "media/templates" ]; then
    echo "📁 Copie de tous les fichiers templates..."
    for file in media/templates/*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            docker cp "$file" "$CONTAINER_NAME:/app/media/templates/$filename"
            echo "   ✅ Copié: $filename"
        fi
    done
fi

echo "✅ Templates copiés avec succès!"
echo "💡 Vous pouvez maintenant tester le téléchargement"
