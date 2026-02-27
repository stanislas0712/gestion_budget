#!/bin/bash
# Script pour copier les templates dans le volume Docker media_volume

echo "📋 Copie des templates dans le volume Docker..."
echo ""

# Vérifier si le conteneur est en cours d'exécution
if ! docker ps | grep -q "budget_web"; then
    echo "❌ Le conteneur budget_web n'est pas en cours d'exécution"
    echo "   Démarrez-le avec: docker-compose up -d web"
    exit 1
fi

# Créer le répertoire templates dans le conteneur
echo "📁 Création du répertoire /app/media/templates..."
docker exec budget_web mkdir -p /app/media/templates

# Vérifier les permissions
echo "🔐 Configuration des permissions..."
docker exec budget_web chmod -R 755 /app/media/templates 2>/dev/null || true

# Liste des templates à copier
TEMPLATES=("template_budget.xlsx" "template_budget.pdf" "template_budget.docx")

# Copier chaque template
echo ""
echo "📄 Copie des templates:"
for template in "${TEMPLATES[@]}"; do
    source_path="media/templates/$template"
    
    if [ -f "$source_path" ]; then
        echo "   Copie de $template..."
        docker cp "$source_path" budget_web:/app/media/templates/
        
        # Vérifier que le fichier a été copié
        if docker exec budget_web test -f "/app/media/templates/$template"; then
            size=$(docker exec budget_web stat -c%s "/app/media/templates/$template" 2>/dev/null || echo "0")
            perms=$(docker exec budget_web ls -l "/app/media/templates/$template" 2>/dev/null | awk '{print $1}')
            echo "      ✅ $template copié (${size} bytes, $perms)"
        else
            echo "      ❌ Erreur lors de la copie de $template"
        fi
    else
        echo "      ⚠️  Fichier source non trouvé: $source_path"
    fi
done

echo ""
echo "📋 Vérification finale:"
docker exec budget_web ls -lah /app/media/templates/

echo ""
echo "🔍 Test d'accès depuis Django:"
docker exec budget_web python manage.py shell << 'EOF'
from django.conf import settings
from pathlib import Path
import os

templates_dir = Path(settings.MEDIA_ROOT) / 'templates'
template_file = templates_dir / 'template_budget.xlsx'

print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
print(f"Template path: {template_file}")
print(f"Existe: {template_file.exists()}")
if template_file.exists():
    print(f"Taille: {template_file.stat().st_size} bytes")
    print(f"Lisible: {os.access(template_file, os.R_OK)}")
EOF

echo ""
echo "✅ Copie terminée!"
