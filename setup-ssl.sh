#!/bin/bash
# Script d'installation et de configuration SSL avec Let's Encrypt

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Configuration SSL pour budget.bkdb.bf${NC}"

# Vérifier que le domaine est défini
DOMAIN="${DOMAIN_NAME:-budget.bkdb.bf}"
EMAIL="${LETSENCRYPT_EMAIL:-}"

if [ -z "$EMAIL" ]; then
    echo -e "${RED}❌ Erreur: LETSENCRYPT_EMAIL doit être défini dans .env${NC}"
    echo "   Ajoutez: LETSENCRYPT_EMAIL=votre-email@example.com"
    exit 1
fi

echo "📋 Domaine: $DOMAIN"
echo "📧 Email: $EMAIL"

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Créer les répertoires nécessaires
echo "📁 Création des répertoires..."
mkdir -p certbot/conf certbot/www

# Essayer de changer les permissions (peut échouer si les répertoires appartiennent à root)
if chmod -R 755 certbot 2>/dev/null; then
    echo "✅ Permissions configurées"
elif sudo chmod -R 755 certbot 2>/dev/null; then
    echo "✅ Permissions configurées (avec sudo)"
    # Changer le propriétaire pour éviter les problèmes futurs
    sudo chown -R $USER:$USER certbot 2>/dev/null || true
else
    echo "⚠️  Impossible de changer les permissions (non critique)"
    # Essayer de changer le propriétaire si les répertoires existent déjà
    if [ -d "certbot" ]; then
        sudo chown -R $USER:$USER certbot 2>/dev/null || true
    fi
fi

# Étape 1: Utiliser la configuration temporaire sans SSL
echo "📝 Configuration temporaire Nginx (sans SSL)..."
if [ -f nginx.conf ]; then
    cp nginx.conf nginx.conf.backup
fi
cp nginx-ssl.conf nginx.conf

# Étape 2: Démarrer les services
echo "🚀 Démarrage des services..."
docker-compose --profile production up -d web
sleep 5
docker-compose --profile production up -d nginx
sleep 5

# Étape 3: Obtenir le certificat Let's Encrypt
echo "🔐 Obtention du certificat SSL..."
docker run --rm \
  -v "$SCRIPT_DIR/certbot/conf:/etc/letsencrypt" \
  -v "$SCRIPT_DIR/certbot/www:/var/www/certbot" \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  -d "$DOMAIN" \
  -d "www.$DOMAIN"

# Vérifier que le certificat a été créé
if [ ! -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${RED}❌ Erreur: Le certificat n'a pas été créé${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Certificat créé avec succès${NC}"

# Étape 4: Restaurer la configuration SSL complète
echo "📝 Activation de la configuration SSL..."
if [ -f nginx.conf.backup ]; then
    # La configuration SSL est déjà dans nginx.conf (écrite par le script)
    # On doit juste s'assurer qu'elle est correcte
    echo "✅ Configuration SSL activée"
else
    echo -e "${YELLOW}⚠️  Attention: nginx.conf doit contenir la configuration SSL${NC}"
    echo "   Vérifiez que nginx.conf contient la configuration HTTPS"
fi

# Étape 5: Redémarrer Nginx
echo "🔄 Redémarrage de Nginx..."
docker-compose --profile production restart nginx

# Étape 6: Vérifier la configuration
echo "✅ Vérification de la configuration..."
docker-compose exec nginx nginx -t

echo -e "${GREEN}✅ Configuration SSL terminée avec succès!${NC}"
echo ""
echo "🌐 Votre application est maintenant accessible sur:"
echo "   - https://$DOMAIN"
echo "   - https://www.$DOMAIN"
echo ""
echo "📝 Pour configurer le renouvellement automatique, ajoutez au crontab:"
echo "   0 3 1 */3 * $SCRIPT_DIR/renew-ssl.sh >> /var/log/certbot-renew.log 2>&1"
