#!/bin/bash
# Script de renouvellement automatique des certificats SSL Let's Encrypt

set -e

echo "🔄 Renouvellement des certificats SSL..."

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Renouveler les certificats
docker run --rm \
  -v "$SCRIPT_DIR/certbot/conf:/etc/letsencrypt" \
  -v "$SCRIPT_DIR/certbot/www:/var/www/certbot" \
  certbot/certbot renew

# Redémarrer Nginx pour charger les nouveaux certificats
if docker-compose ps nginx | grep -q "Up"; then
    echo "🔄 Redémarrage de Nginx..."
    docker-compose restart nginx
    echo "✅ Nginx redémarré avec les nouveaux certificats"
else
    echo "⚠️  Nginx n'est pas en cours d'exécution"
fi

echo "✅ Renouvellement terminé"
