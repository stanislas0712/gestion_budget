#!/bin/bash
# Script pour configurer Nginx manuellement pour budget.bkdb.bf
# Ce script peut être utilisé indépendamment de setup-ssl.sh

set +e  # Ne pas arrêter sur toutes les erreurs

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📝 Configuration de Nginx pour budget.bkdb.bf${NC}"
echo ""

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Charger les variables d'environnement
if [ -f ".env" ]; then
    set -a
    source .env 2>/dev/null || true
    set +a
fi

DOMAIN="${DOMAIN_NAME:-budget.bkdb.bf}"
WEB_PORT="${WEB_PORT:-8000}"

# Vérifier que Nginx est installé
if ! command -v nginx &> /dev/null; then
    echo -e "${RED}❌ Nginx n'est pas installé${NC}"
    echo "   Installez avec: sudo apt install -y nginx"
    exit 1
fi

echo -e "${GREEN}✅ Nginx installé: $(nginx -v 2>&1)${NC}"
echo ""

# Chemin de la configuration
NGINX_SITE="/etc/nginx/sites-available/budget.bkdb.bf"
NGINX_SITE_ENABLED="/etc/nginx/sites-enabled/budget.bkdb.bf"

# Demander le type de configuration
echo -e "${BLUE}Quel type de configuration souhaitez-vous?${NC}"
echo "1. HTTP uniquement (pour obtenir le certificat SSL)"
echo "2. HTTP + HTTPS (avec certificat SSL existant)"
echo "3. HTTPS uniquement (redirection HTTP vers HTTPS)"
read -p "Choix (1-3) [2]: " config_type
config_type=${config_type:-2}

# Créer le répertoire pour les challenges ACME
echo "📁 Création du répertoire pour les challenges..."
sudo mkdir -p /var/www/certbot/.well-known/acme-challenge
sudo chown -R www-data:www-data /var/www/certbot
sudo chmod -R 755 /var/www/certbot
echo -e "${GREEN}✅ Répertoire créé: /var/www/certbot${NC}"
echo ""

# Configuration selon le type choisi
case $config_type in
    1)
        # HTTP uniquement (pour obtenir le certificat)
        echo "📝 Création de la configuration HTTP uniquement..."
        sudo tee "$NGINX_SITE" > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
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
        proxy_pass http://localhost:$WEB_PORT;
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
        echo -e "${GREEN}✅ Configuration HTTP créée${NC}"
        ;;
    2)
        # HTTP + HTTPS (avec certificat SSL)
        if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
            echo -e "${YELLOW}⚠️  Certificat SSL non trouvé dans /etc/letsencrypt/live/$DOMAIN/${NC}"
            echo "   Utilisez l'option 1 pour obtenir le certificat d'abord"
            exit 1
        fi
        
        echo "📝 Création de la configuration HTTP + HTTPS..."
        sudo tee "$NGINX_SITE" > /dev/null <<EOF
# Redirection HTTP vers HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
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
    server_name $DOMAIN www.$DOMAIN;
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
        proxy_pass http://localhost:$WEB_PORT;
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
        echo -e "${GREEN}✅ Configuration HTTP + HTTPS créée${NC}"
        ;;
    3)
        # HTTPS uniquement (redirection HTTP vers HTTPS)
        if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
            echo -e "${YELLOW}⚠️  Certificat SSL non trouvé dans /etc/letsencrypt/live/$DOMAIN/${NC}"
            echo "   Utilisez l'option 1 pour obtenir le certificat d'abord"
            exit 1
        fi
        
        echo "📝 Création de la configuration HTTPS uniquement..."
        sudo tee "$NGINX_SITE" > /dev/null <<EOF
# Redirection HTTP vers HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

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
    server_name $DOMAIN www.$DOMAIN;
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
        proxy_pass http://localhost:$WEB_PORT;
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
        echo -e "${GREEN}✅ Configuration HTTPS créée${NC}"
        ;;
    *)
        echo -e "${RED}❌ Choix invalide${NC}"
        exit 1
        ;;
esac

# Activer le site
echo "🔗 Activation du site..."
sudo ln -sf "$NGINX_SITE" "$NGINX_SITE_ENABLED" 2>/dev/null || true
echo -e "${GREEN}✅ Site activé${NC}"
echo ""

# Tester la configuration
echo "🔍 Test de la configuration Nginx..."
if sudo nginx -t; then
    echo -e "${GREEN}✅ Configuration Nginx valide${NC}"
else
    echo -e "${RED}❌ Erreur dans la configuration Nginx${NC}"
    echo "   Vérifiez le fichier: $NGINX_SITE"
    exit 1
fi
echo ""

# Redémarrer Nginx
read -p "Voulez-vous redémarrer Nginx maintenant? (O/n): " restart_nginx
restart_nginx=${restart_nginx:-O}

if [[ $restart_nginx =~ ^[OoYy]$ ]]; then
    echo "🔄 Redémarrage de Nginx..."
    sudo systemctl reload nginx || sudo systemctl restart nginx
    
    if sudo systemctl is-active --quiet nginx; then
        echo -e "${GREEN}✅ Nginx redémarré avec succès${NC}"
    else
        echo -e "${RED}❌ Erreur lors du redémarrage de Nginx${NC}"
        echo "   Vérifiez les logs: sudo journalctl -u nginx -n 50"
        exit 1
    fi
else
    echo -e "${YELLOW}⏭️  Redémarrage ignoré. Redémarrez manuellement avec:${NC}"
    echo "   sudo systemctl reload nginx"
fi

echo ""
echo -e "${GREEN}✅ Configuration Nginx terminée!${NC}"
echo ""
echo "📋 Fichiers créés:"
echo "   Configuration: $NGINX_SITE"
echo "   Lien activé: $NGINX_SITE_ENABLED"
echo ""
echo "📋 Commandes utiles:"
echo "   Voir la configuration: sudo cat $NGINX_SITE"
echo "   Tester la config: sudo nginx -t"
echo "   Redémarrer: sudo systemctl reload nginx"
echo "   Voir les logs: sudo tail -f /var/log/nginx/budget-error.log"
echo ""
