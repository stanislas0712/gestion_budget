#!/bin/bash
# Script pour vérifier que les templates sont bien présents dans le conteneur

echo "🔍 Vérification des templates dans le conteneur Docker..."

# Vérifier si le conteneur est en cours d'exécution
if ! docker ps | grep -q "budget_web"; then
    echo "❌ Le conteneur budget_web n'est pas en cours d'exécution"
    exit 1
fi

echo ""
echo "📋 Vérification des fichiers templates:"
echo ""

# Vérifier chaque template
TEMPLATES=("template_budget.xlsx" "template_budget.pdf" "template_budget.docx")

for template in "${TEMPLATES[@]}"; do
    echo "Vérification de $template:"
    
    # Vérifier si le fichier existe
    if docker exec budget_web test -f "/app/media/templates/$template" 2>/dev/null; then
        # Obtenir la taille du fichier
        size=$(docker exec budget_web stat -c%s "/app/media/templates/$template" 2>/dev/null || echo "0")
        echo "   ✅ Fichier trouvé: /app/media/templates/$template (${size} bytes)"
        
        # Vérifier les permissions
        perms=$(docker exec budget_web ls -l "/app/media/templates/$template" 2>/dev/null | awk '{print $1}')
        echo "   📝 Permissions: $perms"
    else
        echo "   ❌ Fichier NON trouvé: /app/media/templates/$template"
    fi
    
    echo ""
done

echo "📁 Contenu du répertoire /app/media/templates:"
docker exec budget_web ls -lah /app/media/templates/ 2>/dev/null || echo "   ❌ Répertoire non accessible"

echo ""
echo "📁 Contenu du répertoire /app/media:"
docker exec budget_web ls -lah /app/media/ 2>/dev/null || echo "   ❌ Répertoire non accessible"

echo ""
echo "🔍 Vérification depuis Django (si possible):"
docker exec budget_web python manage.py shell << 'EOF' 2>/dev/null || echo "   ⚠️  Impossible d'exécuter Django shell"
from django.conf import settings
from pathlib import Path

templates_dir = Path(settings.MEDIA_ROOT) / 'templates'
print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
print(f"Templates dir: {templates_dir}")
print(f"Templates dir existe: {templates_dir.exists()}")

if templates_dir.exists():
    print(f"Contenu: {list(templates_dir.iterdir())}")
    for template_file in ['template_budget.xlsx', 'template_budget.pdf', 'template_budget.docx']:
        template_path = templates_dir / template_file
        if template_path.exists():
            size = template_path.stat().st_size
            print(f"  ✅ {template_file}: {size} bytes")
        else:
            print(f"  ❌ {template_file}: NON TROUVÉ")
EOF
