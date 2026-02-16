#!/bin/bash
# Ne pas arrêter sur les erreurs pour permettre la récupération des migrations
set +e

echo "🚀 Démarrage de l'application Budget..."

# Attendre que la base de données soit prête
echo "⏳ Attente de la base de données PostgreSQL..."
if command -v pg_isready > /dev/null 2>&1; then
    while ! pg_isready -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; do
        echo "   En attente de PostgreSQL..."
        sleep 2
    done
    echo "✅ PostgreSQL est prêt!"
else
    echo "⚠️  pg_isready non disponible, attente simple de 5 secondes..."
    sleep 5
fi

# Exécuter les migrations (pour tous les services Django)
echo "📦 Application des migrations..."

# Essayer d'appliquer les migrations normalement
MIGRATE_OUTPUT=$(python manage.py migrate --noinput 2>&1)
MIGRATE_EXIT=$?

if [ $MIGRATE_EXIT -eq 0 ]; then
    echo "✅ Migrations appliquées avec succès"
elif echo "$MIGRATE_OUTPUT" | grep -q "already exists\|duplicate key"; then
    echo "⚠️  Certaines tables existent déjà, marquage des migrations comme appliquées..."
    # Marquer les migrations initiales comme appliquées
    python manage.py migrate --fake-initial --noinput 2>&1 | grep -v "ERROR\|already exists" || true
    # Appliquer les migrations restantes
    python manage.py migrate --noinput 2>&1 | grep -v "ERROR\|already exists" || true
    echo "✅ Migrations synchronisées"
else
    echo "⚠️  Erreurs lors des migrations:"
    echo "$MIGRATE_OUTPUT" | grep "ERROR" | head -5
    echo "💡 L'application va continuer, mais certaines fonctionnalités peuvent ne pas fonctionner"
fi

# Réactiver la gestion d'erreurs pour le reste du script
set -e

# Collecter les fichiers statiques (seulement pour le service web)
if echo "$@" | grep -q "gunicorn"; then
    echo "📁 Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput || true
fi

# Créer un superutilisateur si les variables d'environnement sont définies
if [ -n "$DJANGO_SUPERUSER_PHONE" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "👤 Création du superutilisateur depuis les variables d'environnement..."
    # Utiliser le phone comme username si pas de username spécifique
    export DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-$DJANGO_SUPERUSER_PHONE}
    export DJANGO_SUPERUSER_EMAIL=$DJANGO_SUPERUSER_EMAIL
    export DJANGO_SUPERUSER_PASSWORD=$DJANGO_SUPERUSER_PASSWORD
    
    # Créer le superutilisateur avec createsuperuser --noinput
    python manage.py createsuperuser --noinput || true
    
    # Si le modèle User a un champ phone, l'assigner après création
    if [ -n "$DJANGO_SUPERUSER_PHONE" ]; then
        python manage.py shell << EOF || true
from django.contrib.auth import get_user_model
User = get_user_model()
username = "$DJANGO_SUPERUSER_USERNAME"
phone = "$DJANGO_SUPERUSER_PHONE"

try:
    user = User.objects.get(username=username)
    if hasattr(user, 'phone'):
        user.phone = phone
        user.save()
        print(f'✅ Numéro de téléphone assigné au superutilisateur {username}')
except User.DoesNotExist:
    pass
EOF
    fi
fi

# Créer un superutilisateur par défaut si en développement (fallback)
if [ "$DJANGO_DEBUG" = "1" ] && [ ! -f /app/.superuser_created ] && [ -z "$DJANGO_SUPERUSER_PHONE" ]; then
  echo "👤 Création du superutilisateur par défaut (développement)..."
  python manage.py shell << EOF || true
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superutilisateur créé: admin/admin123')
EOF
  touch /app/.superuser_created
fi

# Exécuter la commande passée en argument
echo "✅ Application prête!"

# Vérifier si des arguments ont été passés
if [ $# -eq 0 ]; then
    echo "⚠️  Aucune commande spécifiée, utilisation de Gunicorn par défaut..."
    COMMAND="gunicorn"
else
    COMMAND="$1"
fi

# Si la commande est gunicorn, utiliser la configuration avancée
if [ "$COMMAND" = "gunicorn" ]; then
    echo "🚀 Démarrage de Gunicorn avec configuration optimisée..."
    exec gunicorn config.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers ${GUNICORN_WORKERS:-4} \
        --threads ${GUNICORN_THREADS:-2} \
        --timeout ${GUNICORN_TIMEOUT:-120} \
        --access-logfile - \
        --error-logfile - \
        --log-level ${GUNICORN_LOG_LEVEL:-info} \
        --worker-class gthread \
        --worker-tmp-dir /dev/shm \
        --preload
else
    # Pour les autres commandes (celery, etc.), exécuter normalement
    echo "🚀 Exécution de la commande: $@"
    exec "$@"
fi
