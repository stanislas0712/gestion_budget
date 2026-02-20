#!/bin/bash
# Script pour résoudre les problèmes de challenge SSL Let's Encrypt

set +e  # Ne pas arrêter sur les erreurs

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Diagnostic et résolution des problèmes de challenge SSL${NC}"
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

echo -e "${BLUE}📋 Vérifications:${NC}"
echo "   Domaine: $DOMAIN"
echo ""

# 1. Vérifier que Nginx est installé et démarré localement
echo -e "${BLUE}1️⃣  Vérification de Nginx...${NC}"
if ! command -v nginx &> /dev/null; then
    echo -e "${RED}❌ Nginx n'est pas installé${NC}"
    echo "   Installez avec: sudo apt install -y nginx"
    exit 1
fi

if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx est démarré (local)${NC}"
    echo "   Version: $(nginx -v 2>&1)"
else
    echo -e "${RED}❌ Nginx n'est pas démarré${NC}"
    echo "   Démarrage de Nginx..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
    sleep 3
    if sudo systemctl is-active --quiet nginx; then
        echo -e "${GREEN}✅ Nginx démarré${NC}"
    else
        echo -e "${RED}❌ Impossible de démarrer Nginx${NC}"
        echo "   Vérifiez les logs: sudo journalctl -u nginx -n 50"
        exit 1
    fi
fi
echo ""

# 2. Vérifier la configuration Nginx pour les challenges
echo -e "${BLUE}2️⃣  Vérification de la configuration Nginx...${NC}"
NGINX_SITE="/etc/nginx/sites-available/budget.bkdb.bf"
NGINX_SITE_ENABLED="/etc/nginx/sites-enabled/budget.bkdb.bf"

if [ -f "$NGINX_SITE" ] && sudo grep -q "/.well-known/acme-challenge" "$NGINX_SITE" 2>/dev/null; then
    echo -e "${GREEN}✅ Configuration ACME trouvée dans $NGINX_SITE${NC}"
elif [ -f "$NGINX_SITE_ENABLED" ] && sudo grep -q "/.well-known/acme-challenge" "$NGINX_SITE_ENABLED" 2>/dev/null; then
    echo -e "${GREEN}✅ Configuration ACME trouvée dans $NGINX_SITE_ENABLED${NC}"
else
    echo -e "${YELLOW}⚠️  Configuration ACME non trouvée${NC}"
    echo "   Le script setup-ssl.sh créera automatiquement la configuration"
fi

# Vérifier la configuration Nginx
if sudo nginx -t 2>/dev/null; then
    echo -e "${GREEN}✅ Configuration Nginx valide${NC}"
else
    echo -e "${RED}❌ Erreur dans la configuration Nginx${NC}"
    sudo nginx -t
fi
echo ""

# 3. Vérifier que le répertoire /var/www/certbot existe et est accessible
echo -e "${BLUE}3️⃣  Vérification du répertoire /var/www/certbot...${NC}"
if [ -d "/var/www/certbot" ]; then
    echo -e "${GREEN}✅ Répertoire /var/www/certbot existe${NC}"
    # Créer un fichier de test
    sudo mkdir -p /var/www/certbot/.well-known/acme-challenge
    echo "test" | sudo tee /var/www/certbot/.well-known/acme-challenge/test.txt > /dev/null
    sudo chown -R www-data:www-data /var/www/certbot
    sudo chmod -R 755 /var/www/certbot
    echo -e "${GREEN}✅ Répertoire accessible${NC}"
else
    echo -e "${RED}❌ Répertoire /var/www/certbot n'existe pas${NC}"
    echo "   Création du répertoire..."
    sudo mkdir -p /var/www/certbot/.well-known/acme-challenge
    sudo chown -R www-data:www-data /var/www/certbot
    sudo chmod -R 755 /var/www/certbot
    echo -e "${GREEN}✅ Répertoire créé${NC}"
fi
echo ""

# 4. Vérifier que Certbot est installé localement
echo -e "${BLUE}4️⃣  Vérification de Certbot...${NC}"
if ! command -v certbot &> /dev/null; then
    echo -e "${RED}❌ Certbot n'est pas installé${NC}"
    echo "   Installez avec: sudo apt install -y certbot python3-certbot-nginx"
else
    echo -e "${GREEN}✅ Certbot installé: $(certbot --version)${NC}"
fi
echo ""

# 5. Tester l'accès HTTP local
echo -e "${BLUE}5️⃣  Test d'accès HTTP local...${NC}"
TEST_FILE="/var/www/certbot/.well-known/acme-challenge/test-$(date +%s).txt"
echo "test-content" | sudo tee "$TEST_FILE" > /dev/null
sudo chmod 644 "$TEST_FILE" 2>/dev/null || true

# Tester l'accès local
if [ -f "$TEST_FILE" ]; then
    echo -e "${GREEN}✅ Fichier créé: $TEST_FILE${NC}"
    # Tester l'accès HTTP
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/.well-known/acme-challenge/$(basename "$TEST_FILE")" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
        echo -e "${GREEN}✅ Fichier accessible via HTTP (code: $HTTP_CODE)${NC}"
    else
        echo -e "${YELLOW}⚠️  Fichier non accessible via HTTP (code: $HTTP_CODE)${NC}"
    fi
    sudo rm -f "$TEST_FILE"
else
    echo -e "${RED}❌ Impossible de créer le fichier de test${NC}"
fi
echo ""

# 6. Vérifier que le port 80 est accessible
echo -e "${BLUE}6️⃣  Vérification de l'accessibilité du port 80...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost/.well-known/acme-challenge/test.txt 2>/dev/null | grep -q "200\|404"; then
    echo -e "${GREEN}✅ Port 80 accessible localement${NC}"
else
    echo -e "${YELLOW}⚠️  Port 80 non accessible localement${NC}"
    echo "   Vérifiez que Nginx écoute sur le port 80"
fi

# Tester depuis l'extérieur
echo "   Test depuis l'extérieur..."
if curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://$DOMAIN/.well-known/acme-challenge/test.txt" 2>/dev/null | grep -q "200\|404"; then
    echo -e "${GREEN}✅ Domaine accessible depuis l'extérieur${NC}"
else
    echo -e "${RED}❌ Domaine non accessible depuis l'extérieur${NC}"
    echo "   Vérifiez:"
    echo "   1. Que le domaine $DOMAIN pointe vers l'IP de ce serveur"
    echo "   2. Que le port 80 est ouvert dans le firewall"
    echo "   3. Que Nginx écoute sur le port 80"
fi
echo ""

# 7. Vérifier le firewall
echo -e "${BLUE}7️⃣  Vérification du firewall...${NC}"
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "80/tcp.*ALLOW"; then
        echo -e "${GREEN}✅ Port 80 ouvert dans UFW${NC}"
    else
        echo -e "${YELLOW}⚠️  Port 80 peut-être fermé dans UFW${NC}"
        echo "   Ouvrir avec: sudo ufw allow 80/tcp"
    fi
elif command -v firewall-cmd &> /dev/null; then
    if firewall-cmd --list-ports 2>/dev/null | grep -q "80/tcp"; then
        echo -e "${GREEN}✅ Port 80 ouvert dans firewalld${NC}"
    else
        echo -e "${YELLOW}⚠️  Port 80 peut-être fermé${NC}"
        echo "   Ouvrir avec: sudo firewall-cmd --permanent --add-service=http"
    fi
else
    echo -e "${YELLOW}⚠️  Aucun firewall détecté${NC}"
fi
echo ""

# 8. Redémarrer Nginx pour appliquer les changements
echo -e "${BLUE}8️⃣  Redémarrage de Nginx...${NC}"
if sudo systemctl is-active --quiet nginx; then
    sudo systemctl reload nginx || sudo systemctl restart nginx
    sleep 3
    if sudo systemctl is-active --quiet nginx; then
        echo -e "${GREEN}✅ Nginx redémarré${NC}"
    else
        echo -e "${RED}❌ Erreur lors du redémarrage de Nginx${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Nginx n'est pas actif${NC}"
fi
echo ""

# 9. Résumé et recommandations
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Diagnostic terminé${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📝 Prochaines étapes:${NC}"
echo ""
echo "1. Vérifiez que le domaine $DOMAIN pointe vers l'IP de ce serveur:"
echo "   dig $DOMAIN +short"
echo "   ou"
echo "   nslookup $DOMAIN"
echo ""
echo "2. Vérifiez que le port 80 est accessible depuis l'extérieur:"
echo "   curl -I http://$DOMAIN"
echo ""
echo "3. Testez manuellement le challenge:"
echo "   echo 'test' | sudo tee /var/www/certbot/.well-known/acme-challenge/test.txt"
echo "   curl http://$DOMAIN/.well-known/acme-challenge/test.txt"
echo ""
echo "4. Si tout est OK, relancez setup-ssl.sh:"
echo "   ./setup-ssl.sh"
echo ""
