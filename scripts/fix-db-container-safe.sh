#!/bin/bash
# Script bash pour résoudre l'erreur ContainerConfig SANS perdre les données

set -e  # Arrêter en cas d'erreur

echo "🔧 Résolution de l'erreur ContainerConfig (mode sécurisé)..."

# Étape 1: Sauvegarder la base de données
echo ""
echo "📋 ÉTAPE 1: Sauvegarde de la base de données"
echo "==========================================="

BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/budget_db_backup_$TIMESTAMP.sql"

# Vérifier que le conteneur existe
if ! docker ps -a --format "{{.Names}}" | grep -q "^budget_db$"; then
    echo "⚠️  Le conteneur budget_db n'existe pas. Passage à l'étape suivante..."
else
    # Vérifier si le conteneur est en cours d'exécution
    if ! docker ps --format "{{.Names}}" | grep -q "^budget_db$"; then
        echo "⚠️  Le conteneur n'est pas en cours d'exécution. Tentative de démarrage..."
        docker start budget_db || true
        sleep 5
    fi
    
    # Lire les variables depuis .env
    DB_NAME="budget"
    DB_USER="budget"
    DB_PASSWORD="budget"
    
    if [ -f ".env" ]; then
        while IFS='=' read -r key value; do
            case "$key" in
                DB_NAME) DB_NAME="${value//\"/}" ;;
                DB_USER) DB_USER="${value//\"/}" ;;
                DB_PASSWORD) DB_PASSWORD="${value//\"/}" ;;
            esac
        done < <(grep -E "^DB_(NAME|USER|PASSWORD)=" .env)
    fi
    
    echo "📊 Base de données: $DB_NAME"
    echo "👤 Utilisateur: $DB_USER"
    echo "💾 Création de la sauvegarde: $BACKUP_FILE"
    
    # Créer la sauvegarde
    PGPASSWORD="$DB_PASSWORD" docker exec budget_db pg_dump -U "$DB_USER" -d "$DB_NAME" -F p > "$BACKUP_FILE" 2>&1
    
    if [ $? -eq 0 ] && [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
        FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "✅ Sauvegarde créée avec succès!"
        echo "   Taille: $FILE_SIZE"
        echo "   Fichier: $BACKUP_FILE"
    else
        echo "⚠️  Échec de la sauvegarde, mais on continue quand même..."
    fi
fi

# Étape 2: Arrêter les conteneurs dépendants
echo ""
echo "📋 ÉTAPE 2: Arrêt des conteneurs dépendants"
echo "==========================================="

echo "🛑 Arrêt des services dépendants..."
docker-compose stop web celery_worker celery_beat 2>/dev/null || true

# Étape 3: Sauvegarder le volume (optionnel mais recommandé)
echo ""
echo "📋 ÉTAPE 3: Sauvegarde du volume Docker"
echo "==========================================="

VOLUME_BACKUP="$BACKUP_DIR/postgres_volume_$TIMESTAMP.tar.gz"
echo "💾 Sauvegarde du volume postgres_data..."

docker run --rm \
    -v budget_postgres_data:/data \
    -v "$(pwd)/$BACKUP_DIR:/backup" \
    alpine tar czf /backup/postgres_volume_backup_$TIMESTAMP.tar.gz -C /data . 2>/dev/null || {
    echo "⚠️  Échec de la sauvegarde du volume, mais la sauvegarde SQL est OK"
}

# Étape 4: Résoudre le problème ContainerConfig
echo ""
echo "📋 ÉTAPE 4: Résolution du problème ContainerConfig"
echo "==========================================="

echo "🗑️  Suppression de tous les conteneurs db problématiques..."

# Supprimer tous les conteneurs avec "budget_db" dans le nom
docker ps -a --filter "name=budget_db" --format "{{.ID}}" | while read -r container_id; do
    echo "   Suppression du conteneur: $container_id"
    docker rm -f "$container_id" 2>/dev/null || true
done

# Supprimer aussi le conteneur avec l'ID problématique mentionné dans l'erreur
docker rm -f 01d17aa4bfb6_budget_db 2>/dev/null || true

# Supprimer tous les conteneurs arrêtés qui pourraient causer des problèmes
docker container prune -f

echo "🧹 Nettoyage des images orphelines..."
docker image prune -f

# Étape 5: Recréer le conteneur
echo ""
echo "📋 ÉTAPE 5: Recréation du conteneur"
echo "==========================================="

echo "🚀 Recréation du conteneur db..."
docker-compose up -d db

# Attendre que le conteneur soit prêt
echo "⏳ Attente du démarrage de PostgreSQL..."
sleep 10

# Vérifier que le conteneur fonctionne
if docker ps --format "{{.Names}}" | grep -q "^budget_db$"; then
    echo "✅ Conteneur db recréé avec succès!"
    
    # Vérifier que les données sont toujours là
    echo "🔍 Vérification des données..."
    sleep 5  # Attendre que PostgreSQL soit complètement prêt
    
    TABLE_COUNT=$(docker exec budget_db psql -U budget -d budget -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ -n "$TABLE_COUNT" ] && [ "$TABLE_COUNT" != "0" ] && [ "$TABLE_COUNT" != "" ]; then
        echo "✅ Les données sont présentes ($TABLE_COUNT tables trouvées)"
    else
        echo "⚠️  Aucune table trouvée ou erreur de connexion."
        echo "💡 Si les données manquent, restaurez la sauvegarde avec:"
        echo "   ./scripts/restaurer-db.sh $BACKUP_FILE"
    fi
else
    echo "❌ Le conteneur n'a pas démarré correctement!"
    echo "📋 Vérifiez les logs: docker-compose logs db"
    exit 1
fi

# Étape 6: Redémarrer les autres services
echo ""
echo "📋 ÉTAPE 6: Redémarrage des autres services"
echo "==========================================="

echo "🚀 Redémarrage des services..."
docker-compose up -d

echo ""
echo "✅ Procédure terminée!"
echo "📊 Vérifiez que tout fonctionne: docker-compose ps"
echo "📋 Voir les logs: docker-compose logs -f"
