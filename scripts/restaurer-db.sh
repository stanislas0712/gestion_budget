#!/bin/bash
# Script bash pour restaurer une sauvegarde de la base de données PostgreSQL

set -e

if [ -z "$1" ]; then
    echo "❌ Usage: $0 <fichier_de_sauvegarde.sql>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Le fichier de sauvegarde n'existe pas: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Restauration de la base de données PostgreSQL..."

# Vérifier que le conteneur db existe et est en cours d'exécution
if ! docker ps --format "{{.Names}}" | grep -q "^budget_db$"; then
    echo "⚠️  Le conteneur budget_db n'est pas en cours d'exécution. Démarrage..."
    docker start budget_db || docker-compose up -d db
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
echo "📁 Fichier de sauvegarde: $BACKUP_FILE"

# Confirmation
read -p "⚠️  Cette opération va ÉCRASER toutes les données actuelles. Continuer? (oui/non): " -r
if [[ ! $REPLY =~ ^[Oo][Uu][Ii]$ ]] && [[ ! $REPLY =~ ^[Oo]$ ]] && [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Opération annulée."
    exit 0
fi

# Restaurer la sauvegarde
echo "🔄 Restauration en cours..."

PGPASSWORD="$DB_PASSWORD" docker exec -i budget_db psql -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Restauration terminée avec succès!"
else
    echo "❌ Erreur lors de la restauration!"
    exit 1
fi
