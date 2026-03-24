#!/bin/bash
# Script de diagnostic complet pour le téléchargement de templates

echo "🔍 Diagnostic du téléchargement de templates"
echo "=============================================="
echo ""

# Vérifier si le conteneur est en cours d'exécution
if ! docker ps | grep -q "budget_web"; then
    echo "❌ Le conteneur budget_web n'est pas en cours d'exécution"
    exit 1
fi

echo "1️⃣  Vérification des fichiers dans le conteneur:"
echo "-----------------------------------------------"
docker exec budget_web ls -lah /app/media/templates/ 2>/dev/null || echo "   ❌ Répertoire non accessible"

echo ""
echo "2️⃣  Vérification des permissions:"
echo "-----------------------------------"
docker exec budget_web ls -ld /app/media/templates/ 2>/dev/null
docker exec budget_web ls -l /app/media/templates/template_budget.xlsx 2>/dev/null || echo "   ❌ Fichier non trouvé"

echo ""
echo "3️⃣  Vérification depuis Django:"
echo "----------------------------------"
docker exec budget_web python manage.py shell << 'EOF'
from django.conf import settings
from pathlib import Path
import os

print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
print(f"MEDIA_URL: {settings.MEDIA_URL}")

templates_dir = Path(settings.MEDIA_ROOT) / 'templates'
print(f"\nTemplates dir: {templates_dir}")
print(f"Templates dir existe: {templates_dir.exists()}")

if templates_dir.exists():
    print(f"Contenu: {list(templates_dir.iterdir())}")
    for template_file in ['template_budget.xlsx', 'template_budget.pdf', 'template_budget.docx']:
        template_path = templates_dir / template_file
        if template_path.exists():
            size = template_path.stat().st_size
            readable = os.access(template_path, os.R_OK)
            print(f"  ✅ {template_file}: {size} bytes, readable: {readable}")
        else:
            print(f"  ❌ {template_file}: NON TROUVÉ")
else:
    print("  ❌ Le répertoire templates n'existe pas")
    
    # Vérifier le répertoire parent
    media_dir = Path(settings.MEDIA_ROOT)
    print(f"\nMedia dir: {media_dir}")
    print(f"Media dir existe: {media_dir.exists()}")
    if media_dir.exists():
        print(f"Contenu de media: {list(media_dir.iterdir())}")
EOF

echo ""
echo "4️⃣  Test de l'URL de téléchargement:"
echo "--------------------------------------"
echo "Test depuis le conteneur:"
docker exec budget_web curl -I http://localhost:8000/budgets/telecharger-template/excel/ 2>/dev/null | head -10 || echo "   ❌ Erreur lors du test"

echo ""
echo "5️⃣  Vérification des logs Django:"
echo "----------------------------------"
echo "Dernières lignes des logs contenant 'template' ou 'telecharger':"
docker-compose logs web | grep -i -E "(template|telecharger)" | tail -20 || echo "   Aucun log trouvé"

echo ""
echo "6️⃣  Vérification du volume Docker:"
echo "-----------------------------------"
echo "Informations sur le volume media_volume:"
docker volume inspect budget_media_volume 2>/dev/null || echo "   ⚠️  Volume non trouvé ou nom différent"

echo ""
echo "✅ Diagnostic terminé"
echo ""
echo "💡 Si les fichiers sont manquants, exécutez:"
echo "   ./copy-templates-to-volume.sh"
