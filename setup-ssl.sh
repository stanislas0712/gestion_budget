#!/bin/bash
# Script d'installation et de configuration SSL avec Let's Encrypt
# Nginx et Certbot doivent être installés localement sur le serveur Ubuntu

set +e  # Ne pas arrêter sur toutes les erreurs

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Configuration SSL pour budget.bkdb.bf${NC}"
echo -e "${BLUE}📋 Nginx et Certbot doivent être installés localement sur le serveur${NC}"
echo ""

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

# Vérifier que Nginx est installé localement
echo "🔍 Vérification de Nginx..."
if ! command -v nginx &> /dev/null; then
    echo -e "${RED}❌ Nginx n'est pas installé${NC}"
    echo "   Installez avec: sudo apt install -y nginx"
    exit 1
fi
echo -e "${GREEN}✅ Nginx installé: $(nginx -v 2>&1)${NC}"

# Vérifier que Certbot est installé localement
echo "🔍 Vérification de Certbot..."
if ! command -v certbot &> /dev/null; then
    echo -e "${RED}❌ Certbot n'est pas installé${NC}"
    echo "   Installez avec: sudo apt install -y certbot python3-certbot-nginx"
    exit 1
fi
echo -e "${GREEN}✅ Certbot installé: $(certbot --version)${NC}"

# Créer le répertoire pour les challenges ACME
echo "📁 Création du répertoire pour les challenges..."
sudo mkdir -p /var/www/certbot/.well-known/acme-challenge
sudo chown -R www-data:www-data /var/www/certbot
sudo chmod -R 755 /var/www/certbot
echo -e "${GREEN}✅ Répertoire créé: /var/www/certbot${NC}"

# Étape 1: Configurer Nginx pour les challenges ACME
echo "📝 Configuration de Nginx pour les challenges ACME..."

# Créer la configuration Nginx pour le domaine
NGINX_SITE="/etc/nginx/sites-available/budget.bkdb.bf"
NGINX_SITE_ENABLED="/etc/nginx/sites-enabled/budget.bkdb.bf"

# Créer la configuration temporaire (HTTP uniquement pour le challenge)
sudo tee "$NGINX_SITE" > /dev/null <<EOF
server {
    listen 80;
    server_name budget.bkdb.bf www.budget.bkdb.bf;
    client_max_body_size 100M;

    # Logs
    access_log /var/log/nginx/budget-access.log;
    error_log /var/log/nginx/budget-error.log;

    # Acme Challenge pour Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Proxy vers Django (Docker)
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Activer le site
sudo ln -sf "$NGINX_SITE" "$NGINX_SITE_ENABLED" 2>/dev/null || true

# Tester la configuration Nginx
echo "🔍 Test de la configuration Nginx..."
if sudo nginx -t; then
    echo -e "${GREEN}✅ Configuration Nginx valide${NC}"
else
    echo -e "${RED}❌ Erreur dans la configuration Nginx${NC}"
    exit 1
fi

# Étape 2: Démarrer/Redémarrer Nginx
echo "🚀 Démarrage/Redémarrage de Nginx..."
if sudo systemctl is-active --quiet nginx; then
    echo "   Redémarrage de Nginx..."
    sudo systemctl reload nginx || sudo systemctl restart nginx
else
    echo "   Démarrage de Nginx..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
fi

sleep 3

# Vérifier que Nginx est actif
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx est actif${NC}"
else
    echo -e "${RED}❌ Erreur: Nginx n'est pas actif${NC}"
    echo "   Vérifiez les logs: sudo journalctl -u nginx -n 50"
    exit 1
fi

# Vérifier que le service web Django (Docker) est démarré
echo "🔍 Vérification du service web Django..."
if docker-compose ps web 2>/dev/null | grep -q "Up"; then
    echo -e "${GREEN}✅ Service web Django démarré${NC}"
else
    echo -e "${YELLOW}⚠️  Service web Django non démarré, démarrage...${NC}"
    docker-compose --profile production up -d web
    sleep 5
fi

# Vérifier que le domaine pointe vers ce serveur
echo "🔍 Vérification du domaine $DOMAIN..."
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "non détecté")
DOMAIN_IP=$(dig +short "$DOMAIN" 2>/dev/null | tail -1 || nslookup "$DOMAIN" 2>/dev/null | grep -A1 "Name:" | tail -1 | awk '{print $2}' || echo "non détecté")

if [ "$SERVER_IP" != "non détecté" ] && [ "$DOMAIN_IP" != "non détecté" ]; then
    if [ "$SERVER_IP" = "$DOMAIN_IP" ]; then
        echo -e "${GREEN}✅ Le domaine $DOMAIN pointe vers ce serveur ($SERVER_IP)${NC}"
    else
        echo -e "${YELLOW}⚠️  Le domaine $DOMAIN pointe vers $DOMAIN_IP mais ce serveur est $SERVER_IP${NC}"
        echo "   Vérifiez votre configuration DNS"
    fi
else
    echo -e "${YELLOW}⚠️  Impossible de vérifier le DNS automatiquement${NC}"
fi

# Tester l'accès HTTP local
echo "🔍 Test de l'accès HTTP local..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost/.well-known/acme-challenge/test 2>/dev/null | grep -qE "200|404|301"; then
    echo -e "${GREEN}✅ Nginx accessible localement${NC}"
else
    echo -e "${YELLOW}⚠️  Nginx peut ne pas être accessible localement${NC}"
fi

echo ""
echo "⏳ Attente pour que Nginx soit complètement prêt..."
sleep 5

# Étape 3: Vérifier que le répertoire de challenge est accessible
echo "🔍 Vérification du répertoire de challenge..."
if [ -d "/var/www/certbot/.well-known/acme-challenge" ]; then
    echo -e "${GREEN}✅ Répertoire /var/www/certbot/.well-known/acme-challenge existe${NC}"
    
    # Tester l'écriture
    TEST_FILE="/var/www/certbot/.well-known/acme-challenge/test-$(date +%s).txt"
    if echo "test" | sudo tee "$TEST_FILE" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Répertoire accessible en écriture${NC}"
        sudo rm -f "$TEST_FILE"
    else
        echo -e "${YELLOW}⚠️  Problème d'accès au répertoire${NC}"
        sudo chown -R www-data:www-data /var/www/certbot
        sudo chmod -R 755 /var/www/certbot
    fi
else
    echo -e "${RED}❌ Répertoire manquant, création...${NC}"
    sudo mkdir -p /var/www/certbot/.well-known/acme-challenge
    sudo chown -R www-data:www-data /var/www/certbot
    sudo chmod -R 755 /var/www/certbot
fi

# Étape 4: Obtenir le certificat Let's Encrypt avec Certbot local
echo "🔐 Obtention du certificat SSL avec Certbot..."
echo "   Cela peut prendre 1-2 minutes..."
echo ""

if sudo certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  -d "$DOMAIN" \
  -d "www.$DOMAIN" 2>&1 | tee /tmp/certbot-output.log; then
    echo ""
    echo -e "${GREEN}✅ Certificat obtenu avec succès${NC}"
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
        echo "1. Vérifiez que Nginx est démarré: sudo systemctl status nginx"
        echo "2. Vérifiez les logs Nginx: sudo tail -f /var/log/nginx/error.log"
        echo "3. Testez manuellement: curl http://$DOMAIN/.well-known/acme-challenge/test"
        echo "4. Utilisez le script de diagnostic: ./fix-ssl-challenge.sh"
        echo ""
        echo "Vérifications rapides:"
        echo "  - Port 80 ouvert: sudo ufw status | grep 80"
        echo "  - Nginx écoute: sudo netstat -tlnp | grep :80"
        echo "  - DNS correct: dig $DOMAIN +short"
    fi
    rm -f /tmp/certbot-output.log
    exit 1
fi
rm -f /tmp/certbot-output.log

# Vérifier que le certificat a été créé
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${RED}❌ Erreur: Le certificat n'a pas été créé${NC}"
    echo ""
    echo "Vérifiez:"
    echo "1. Que Nginx est accessible sur http://$DOMAIN"
    echo "2. Que le répertoire /.well-known/acme-challenge/ est accessible"
    echo "3. Utilisez: ./fix-ssl-challenge.sh pour diagnostiquer"
    exit 1
fi

echo -e "${GREEN}✅ Certificat créé avec succès${NC}"

# Étape 5: Mettre à jour la configuration Nginx pour HTTPS
echo "📝 Configuration Nginx pour HTTPS..."

# Mettre à jour la configuration Nginx avec SSL
sudo tee "$NGINX_SITE" > /dev/null <<EOF
# Redirection HTTP vers HTTPS
server {
    listen 80;
    server_name budget.bkdb.bf www.budget.bkdb.bf;
    client_max_body_size 100M;

    # Logs
    access_log /var/log/nginx/budget-access.log;
    error_log /var/log/nginx/budget-error.log;

    # Acme Challenge pour Let's Encrypt (renouvellement)
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirection vers HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Configuration HTTPS
server {
    listen 443 ssl http2;
    server_name budget.bkdb.bf www.budget.bkdb.bf;
    client_max_body_size 100M;

    # Logs
    access_log /var/log/nginx/budget-ssl-access.log;
    error_log /var/log/nginx/budget-ssl-error.log;

    # Certificats SSL Let's Encrypt
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # Configuration SSL moderne et sécurisée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Headers de sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy vers Django (Docker)
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Tester la configuration
echo "🔍 Test de la configuration Nginx..."
if sudo nginx -t; then
    echo -e "${GREEN}✅ Configuration Nginx valide${NC}"
else
    echo -e "${RED}❌ Erreur dans la configuration Nginx${NC}"
    exit 1
fi

# Étape 6: Redémarrer Nginx
echo "🔄 Redémarrage de Nginx..."
sudo systemctl reload nginx || sudo systemctl restart nginx

# Vérifier que Nginx est toujours actif
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx redémarré avec succès${NC}"
else
    echo -e "${RED}❌ Erreur: Nginx n'est pas actif après redémarrage${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration SSL terminée avec succès!${NC}"
echo ""
echo "🌐 Votre application est maintenant accessible sur:"
echo "   - https://$DOMAIN"
echo "   - https://www.$DOMAIN"
echo ""
echo "📝 Pour configurer le renouvellement automatique, ajoutez au crontab:"
echo "   0 3 1 */3 * $SCRIPT_DIR/renew-ssl.sh >> /var/log/certbot-renew.log 2>&1"
