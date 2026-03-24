#!/bin/bash
# Script de correction des permissions pour certbot

set -e

echo "🔧 Correction des permissions pour certbot..."

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Créer les répertoires s'ils n'existent pas
mkdir -p certbot/conf certbot/www

# Changer le propriétaire
echo "📝 Changement du propriétaire..."
if sudo chown -R $USER:$USER certbot 2>/dev/null; then
    echo "✅ Propriétaire changé"
else
    echo "⚠️  Impossible de changer le propriétaire (peut nécessiter sudo)"
    exit 1
fi

# Changer les permissions
echo "📝 Configuration des permissions..."
if chmod -R 755 certbot; then
    echo "✅ Permissions configurées"
else
    echo "❌ Erreur lors de la configuration des permissions"
    exit 1
fi

echo ""
echo "✅ Permissions corrigées avec succès!"
echo "   Vous pouvez maintenant exécuter ./setup-ssl.sh"
