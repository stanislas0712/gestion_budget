#!/bin/bash
# Script pour corriger les problèmes de migrations Django

echo "🔧 Correction des migrations Django..."
echo ""

# Vérifier que docker-compose est disponible
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose n'est pas installé"
    exit 1
fi

# Vérifier que le conteneur est en cours d'exécution
if ! docker-compose ps | grep -q "budget_web.*Up"; then
    echo "⚠️  Le conteneur web n'est pas en cours d'exécution"
    echo "💡 Démarrez-le avec: docker-compose up -d"
    exit 1
fi

echo "📦 État actuel des migrations:"
docker-compose exec web python manage.py showmigrations | head -20

echo ""
echo "🔧 Marquage de toutes les migrations comme appliquées (--fake)..."
docker-compose exec web python manage.py migrate --fake --noinput

echo ""
echo "📦 Application des nouvelles migrations (si nécessaire)..."
docker-compose exec web python manage.py migrate --noinput

echo ""
echo "✅ Vérification finale:"
docker-compose exec web python manage.py showmigrations | grep "\[ \]" | head -10

if [ $? -eq 0 ]; then
    echo "⚠️  Il reste des migrations non appliquées (voir ci-dessus)"
else
    echo "✅ Toutes les migrations sont appliquées"
fi

echo ""
echo "✅ Correction terminée !"
