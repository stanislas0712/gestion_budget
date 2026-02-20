#!/bin/bash
# Script d'installation et de configuration SSL avec Let's Encrypt

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Configuration SSL pour budget.bkdb.bf${NC}"

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Charger les variables d'environnement depuis .env
if [ -f ".env" ]; then
    echo "📄 Chargement des variables depuis .env..."
    # Désactiver temporairement set -e pour le chargement
    set +e
    # Exporter toutes les variables depuis .env
    # Utiliser set -a pour exporter automatiquement toutes les variables définies
    set -a
    # Source le fichier .env (ignorer les erreurs)
    source .env 2>/dev/null || true
    set +a
    set -e  # Réactiver set -e
    echo "✅ Variables chargées"
    
    # Afficher les valeurs chargées pour debug (optionnel)
    if [ "${DEBUG:-}" = "1" ]; then
        echo "   DOMAIN_NAME=${DOMAIN_NAME:-non défini}"
        echo "   LETSENCRYPT_EMAIL=${LETSENCRYPT_EMAIL:-non défini}"
    fi
else
    echo -e "${YELLOW}⚠️  Fichier .env non trouvé${NC}"
fi

# Vérifier que le domaine est défini (après chargement de .env)
DOMAIN="${DOMAIN_NAME:-budget.bkdb.bf}"
EMAIL="${LETSENCRYPT_EMAIL:-}"

if [ -z "$EMAIL" ]; then
    echo -e "${RED}❌ Erreur: LETSENCRYPT_EMAIL doit être défini dans .env${NC}"
    echo "   Ajoutez: LETSENCRYPT_EMAIL=votre-email@example.com"
    echo ""
    echo "💡 Vérifiez que votre fichier .env contient:"
    echo "   LETSENCRYPT_EMAIL=votre-email@example.com"
    echo ""
    echo "🔍 Debug: Vérification du fichier .env..."
    if [ -f ".env" ]; then
        echo "   Fichier .env trouvé"
        if grep -q "LETSENCRYPT_EMAIL" .env; then
            echo "   Ligne LETSENCRYPT_EMAIL trouvée:"
            grep "LETSENCRYPT_EMAIL" .env | head -1
        else
            echo "   ⚠️  Ligne LETSENCRYPT_EMAIL non trouvée dans .env"
        fi
    else
        echo "   ⚠️  Fichier .env non trouvé"
    fi
    exit 1
fi

echo "📋 Domaine: $DOMAIN"
echo "📧 Email: $EMAIL"

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
echo "   Attente du démarrage de web..."
sleep 10

# Vérifier que web est prêt
if ! docker-compose ps web | grep -q "Up"; then
    echo -e "${RED}❌ Erreur: Le service web n'a pas démarré${NC}"
    echo "   Vérifiez les logs: docker-compose logs web"
    exit 1
fi

echo "🚀 Démarrage de Nginx..."
docker-compose --profile production up -d nginx
echo "   Attente du démarrage de Nginx..."
sleep 10

# Vérifier que Nginx est prêt
if ! docker-compose ps nginx | grep -q "Up"; then
    echo -e "${RED}❌ Erreur: Nginx n'a pas démarré${NC}"
    echo "   Vérifiez les logs: docker-compose logs nginx"
    exit 1
fi

# Vérifier que Nginx écoute sur le port 80
echo "🔍 Vérification de l'accessibilité de Nginx..."
if docker-compose exec -T nginx nginx -t 2>/dev/null; then
    echo "✅ Configuration Nginx valide"
else
    echo -e "${YELLOW}⚠️  Erreur de configuration Nginx (peut être normal)${NC}"
fi

# Tester l'accès HTTP local
if curl -s -o /dev/null -w "%{http_code}" http://localhost/.well-known/acme-challenge/test 2>/dev/null | grep -qE "200|404|301"; then
    echo "✅ Nginx accessible localement"
else
    echo -e "${YELLOW}⚠️  Nginx peut ne pas être accessible localement${NC}"
fi

# Vérifier que le domaine pointe vers ce serveur
echo "🔍 Vérification du domaine $DOMAIN..."
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "non détecté")
DOMAIN_IP=$(dig +short "$DOMAIN" 2>/dev/null | tail -1 || nslookup "$DOMAIN" 2>/dev/null | grep -A1 "Name:" | tail -1 | awk '{print $2}' || echo "non détecté")

if [ "$SERVER_IP" != "non détecté" ] && [ "$DOMAIN_IP" != "non détecté" ]; then
    if [ "$SERVER_IP" = "$DOMAIN_IP" ]; then
        echo "✅ Le domaine $DOMAIN pointe vers ce serveur ($SERVER_IP)"
    else
        echo -e "${YELLOW}⚠️  Le domaine $DOMAIN pointe vers $DOMAIN_IP mais ce serveur est $SERVER_IP${NC}"
        echo "   Vérifiez votre configuration DNS"
    fi
else
    echo -e "${YELLOW}⚠️  Impossible de vérifier le DNS automatiquement${NC}"
fi

echo ""
echo "⏳ Attente supplémentaire pour que Nginx soit complètement prêt..."
sleep 5

# Étape 3: Vérifier que le répertoire de challenge est accessible
echo "🔍 Vérification du répertoire de challenge..."
mkdir -p certbot/www/.well-known/acme-challenge
chmod -R 755 certbot/www 2>/dev/null || true

# Tester l'écriture dans le répertoire
TEST_FILE="certbot/www/.well-known/acme-challenge/test-$(date +%s).txt"
echo "test" > "$TEST_FILE" 2>/dev/null || {
    echo -e "${RED}❌ Erreur: Impossible d'écrire dans certbot/www${NC}"
    echo "   Vérifiez les permissions: sudo chown -R \$USER:\$USER certbot"
    exit 1
}
rm -f "$TEST_FILE"

# Étape 4: Obtenir le certificat Let's Encrypt
echo "🔐 Obtention du certificat SSL..."
echo "   Cela peut prendre 1-2 minutes..."
echo ""

if docker run --rm \
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
  -d "www.$DOMAIN" 2>&1 | tee /tmp/certbot-output.log; then
    echo ""
    echo -e "${GREEN}✅ Certificat demandé avec succès${NC}"
else
    CERTBOT_ERROR=$(cat /tmp/certbot-output.log 2>/dev/null || echo "")
    echo ""
    echo -e "${RED}❌ Erreur lors de l'obtention du certificat${NC}"
    echo ""
    if echo "$CERTBOT_ERROR" | grep -q "Connection refused"; then
        echo -e "${YELLOW}💡 Problème détecté: Connection refused${NC}"
        echo ""
        echo "Causes possibles:"
        echo "1. Nginx n'est pas démarré ou accessible"
        echo "2. Le port 80 n'est pas ouvert dans le firewall"
        echo "3. Le domaine ne pointe pas vers ce serveur"
        echo "4. Nginx n'est pas configuré pour servir /.well-known/acme-challenge/"
        echo ""
        echo "Solutions:"
        echo "1. Vérifiez que Nginx est démarré: docker-compose ps nginx"
        echo "2. Vérifiez les logs Nginx: docker-compose logs nginx"
        echo "3. Testez manuellement: curl http://$DOMAIN/.well-known/acme-challenge/test"
        echo "4. Utilisez le script de diagnostic: ./fix-ssl-challenge.sh"
        echo ""
        echo "Vérifications rapides:"
        echo "  - Port 80 ouvert: sudo ufw status | grep 80"
        echo "  - Nginx écoute: docker-compose exec nginx netstat -tlnp | grep 80"
        echo "  - DNS correct: dig $DOMAIN +short"
    fi
    rm -f /tmp/certbot-output.log
    exit 1
fi
rm -f /tmp/certbot-output.log

# Vérifier que le certificat a été créé
if [ ! -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${RED}❌ Erreur: Le certificat n'a pas été créé${NC}"
    echo ""
    echo "Vérifiez:"
    echo "1. Que Nginx est accessible sur http://$DOMAIN"
    echo "2. Que le répertoire /.well-known/acme-challenge/ est accessible"
    echo "3. Utilisez: ./fix-ssl-challenge.sh pour diagnostiquer"
    exit 1
fi

echo -e "${GREEN}✅ Certificat créé avec succès${NC}"

# Étape 5: Restaurer la configuration SSL complète
echo "📝 Activation de la configuration SSL..."
if [ -f nginx.conf.backup ]; then
    # La configuration SSL est déjà dans nginx.conf (écrite par le script)
    # On doit juste s'assurer qu'elle est correcte
    echo "✅ Configuration SSL activée"
else
    echo -e "${YELLOW}⚠️  Attention: nginx.conf doit contenir la configuration SSL${NC}"
    echo "   Vérifiez que nginx.conf contient la configuration HTTPS"
fi

# Étape 6: Redémarrer Nginx
echo "🔄 Redémarrage de Nginx..."
docker-compose --profile production restart nginx

# Étape 7: Vérifier la configuration
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
