#!/bin/bash
# Ne pas arrêter sur les erreurs pour permettre la récupération des migrations
set +e

# Activer le virtualenv si il existe
if [ -f /opt/venv/bin/activate ]; then
    source /opt/venv/bin/activate
fi

# Ajouter le virtualenv au PATH si les binaires existent
if [ -d /opt/venv/bin ]; then
    export PATH="/opt/venv/bin:$PATH"
fi

# Définir les commandes Python et Gunicorn
PYTHON_CMD=$(which python || echo "/opt/venv/bin/python")
GUNICORN_CMD=$(which gunicorn || echo "/opt/venv/bin/gunicorn")

echo "🚀 Démarrage de l'application Budget..."
echo "✅ Python: $PYTHON_CMD ($($PYTHON_CMD --version 2>&1))"
echo "✅ Gunicorn: $GUNICORN_CMD"

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
MIGRATE_OUTPUT=$($PYTHON_CMD manage.py migrate --noinput 2>&1)
MIGRATE_EXIT=$?

if [ $MIGRATE_EXIT -eq 0 ]; then
    echo "✅ Migrations appliquées avec succès"
elif echo "$MIGRATE_OUTPUT" | grep -q "already exists\|duplicate key"; then
    echo "⚠️  Certaines tables existent déjà, marquage des migrations comme appliquées..."
    # Marquer les migrations initiales comme appliquées
    $PYTHON_CMD manage.py migrate --fake-initial --noinput 2>&1 | grep -v "ERROR\|already exists" || true
    # Appliquer les migrations restantes
    $PYTHON_CMD manage.py migrate --noinput 2>&1 | grep -v "ERROR\|already exists" || true
    echo "✅ Migrations synchronisées"
else
    echo "⚠️  Erreurs lors des migrations:"
    echo "$MIGRATE_OUTPUT" | grep "ERROR" | head -5
    echo "💡 L'application va continuer, mais certaines fonctionnalités peuvent ne pas fonctionner"
fi

# Ne pas réactiver set -e ici pour permettre la création du superutilisateur même en cas d'erreur mineure
# set -e sera réactivé juste avant l'exécution de la commande finale

# Collecter les fichiers statiques (seulement pour le service web)
if echo "$@" | grep -q "gunicorn"; then
    echo "📁 Collecte des fichiers statiques..."
    $PYTHON_CMD manage.py collectstatic --noinput || true
fi

# Créer un superutilisateur si les variables d'environnement sont définies
# Vérifier si au moins EMAIL et PASSWORD sont définis (PHONE est optionnel)
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "👤 Création du superutilisateur depuis les variables d'environnement..."
    # Utiliser le username fourni, ou le phone si disponible, ou 'admin' par défaut
    export DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-${DJANGO_SUPERUSER_PHONE:-admin}}
    export DJANGO_SUPERUSER_EMAIL=$DJANGO_SUPERUSER_EMAIL
    export DJANGO_SUPERUSER_PASSWORD=$DJANGO_SUPERUSER_PASSWORD
    
    echo "   Username: $DJANGO_SUPERUSER_USERNAME"
    echo "   Email: $DJANGO_SUPERUSER_EMAIL"
    
    # Créer le superutilisateur avec createsuperuser --noinput
    $PYTHON_CMD manage.py createsuperuser --noinput 2>&1 || {
        echo "⚠️  Erreur lors de la création du superutilisateur (peut-être qu'il existe déjà)"
    }
    
    # Si le modèle User a un champ phone, l'assigner après création
    if [ -n "$DJANGO_SUPERUSER_PHONE" ]; then
        $PYTHON_CMD manage.py shell << EOF || true
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
    echo "✅ Superutilisateur créé ou mis à jour"
fi

# Créer un superutilisateur par défaut si aucun superutilisateur n'existe (fallback)
echo "👤 Vérification et création du superutilisateur..."
# Utiliser les variables d'environnement si disponibles, sinon valeurs par défaut
DEFAULT_USERNAME=${DJANGO_SUPERUSER_USERNAME:-Benkadibaara}
DEFAULT_EMAIL=${DJANGO_SUPERUSER_EMAIL:-rapenegsama@gmail.com}
DEFAULT_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-P@ssw0rd75675420}

$PYTHON_CMD manage.py shell << EOF || true
from django.contrib.auth import get_user_model
User = get_user_model()

username = "$DEFAULT_USERNAME"
email = "$DEFAULT_EMAIL"
password = "$DEFAULT_PASSWORD"
phone = "$DJANGO_SUPERUSER_PHONE"

# Vérifier s'il existe déjà un superutilisateur
has_superuser = User.objects.filter(is_superuser=True).exists()

if not has_superuser:
    # Créer le superutilisateur
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(username, email, password)
        print(f'✅ Superutilisateur créé: {username}/{password}')
    else:
        # Si l'utilisateur existe mais n'est pas superuser, le promouvoir
        user = User.objects.get(username=username)
        user.is_superuser = True
        user.is_staff = True
        user.set_password(password)
        user.save()
        print(f'✅ Utilisateur {username} promu au rang de superutilisateur')
    
    # Assigner le numéro de téléphone si disponible et si le champ existe
    if phone:
        try:
            user = User.objects.get(username=username)
            if hasattr(user, 'phone'):
                user.phone = phone
                user.save()
                print(f'✅ Numéro de téléphone assigné: {phone}')
        except User.DoesNotExist:
            pass
else:
    print(f'ℹ️  Un superutilisateur existe déjà')
    # Vérifier si l'utilisateur par défaut existe et est superuser
    if User.objects.filter(username=username, is_superuser=True).exists():
        print(f'ℹ️  Superutilisateur {username} existe déjà')
    elif User.objects.filter(username=username).exists():
        # Promouvoir l'utilisateur existant
        user = User.objects.get(username=username)
        user.is_superuser = True
        user.is_staff = True
        if password != "admin123":  # Ne changer le mot de passe que si différent du défaut
            user.set_password(password)
        user.save()
        print(f'✅ Utilisateur {username} promu au rang de superutilisateur')
EOF
echo "✅ Vérification du superutilisateur terminée"

# Réactiver la gestion d'erreurs pour l'exécution de la commande finale
set -e

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
    exec $GUNICORN_CMD config.wsgi:application \
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
