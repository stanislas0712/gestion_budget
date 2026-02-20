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

# 1. Vérifier que Nginx est démarré
echo -e "${BLUE}1️⃣  Vérification de Nginx...${NC}"
if docker-compose ps nginx | grep -q "Up"; then
    echo -e "${GREEN}✅ Nginx est démarré${NC}"
else
    echo -e "${RED}❌ Nginx n'est pas démarré${NC}"
    echo "   Démarrage de Nginx..."
    docker-compose --profile production up -d nginx
    sleep 5
    if docker-compose ps nginx | grep -q "Up"; then
        echo -e "${GREEN}✅ Nginx démarré${NC}"
    else
        echo -e "${RED}❌ Impossible de démarrer Nginx${NC}"
        echo "   Vérifiez les logs: docker-compose logs nginx"
        exit 1
    fi
fi
echo ""

# 2. Vérifier la configuration Nginx pour les challenges
echo -e "${BLUE}2️⃣  Vérification de la configuration Nginx...${NC}"
if grep -q "/.well-known/acme-challenge" nginx.conf 2>/dev/null; then
    echo -e "${GREEN}✅ Configuration ACME trouvée dans nginx.conf${NC}"
else
    echo -e "${RED}❌ Configuration ACME manquante dans nginx.conf${NC}"
    echo "   Ajout de la configuration..."
    
    # Créer une sauvegarde
    cp nginx.conf nginx.conf.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    
    # Vérifier si nginx.conf existe et contient déjà un serveur sur le port 80
    if [ -f "nginx.conf" ] && grep -q "listen 80" nginx.conf; then
        # Ajouter la location pour ACME si elle n'existe pas
        if ! grep -q "/.well-known/acme-challenge" nginx.conf; then
            # Insérer la location avant la redirection
            sed -i '/location \//i\        location /.well-known/acme-challenge/ {\n            root /var/www/certbot;\n        }' nginx.conf 2>/dev/null || {
                echo -e "${YELLOW}⚠️  Impossible de modifier nginx.conf automatiquement${NC}"
                echo "   Ajoutez manuellement dans nginx.conf:"
                echo "   location /.well-known/acme-challenge/ {"
                echo "       root /var/www/certbot;"
                echo "   }"
            }
        fi
    else
        echo -e "${YELLOW}⚠️  Configuration HTTP manquante${NC}"
        echo "   Utilisez nginx-ssl.conf comme base pour la configuration temporaire"
    fi
fi
echo ""

# 3. Vérifier que le répertoire certbot/www existe et est accessible
echo -e "${BLUE}3️⃣  Vérification du répertoire certbot/www...${NC}"
if [ -d "certbot/www" ]; then
    echo -e "${GREEN}✅ Répertoire certbot/www existe${NC}"
    # Créer un fichier de test
    mkdir -p certbot/www/.well-known/acme-challenge
    echo "test" > certbot/www/.well-known/acme-challenge/test.txt
    chmod -R 755 certbot/www 2>/dev/null || true
    echo -e "${GREEN}✅ Répertoire accessible${NC}"
else
    echo -e "${RED}❌ Répertoire certbot/www n'existe pas${NC}"
    echo "   Création du répertoire..."
    mkdir -p certbot/www/.well-known/acme-challenge
    chmod -R 755 certbot/www
    echo -e "${GREEN}✅ Répertoire créé${NC}"
fi
echo ""

# 4. Vérifier que le volume est bien monté dans Nginx
echo -e "${BLUE}4️⃣  Vérification du montage du volume dans Nginx...${NC}"
if docker-compose --profile production config | grep -q "certbot/www"; then
    echo -e "${GREEN}✅ Volume certbot/www monté${NC}"
else
    echo -e "${YELLOW}⚠️  Volume certbot/www non trouvé dans docker-compose.yml${NC}"
    echo "   Vérifiez que docker-compose.yml contient:"
    echo "   volumes:"
    echo "     - ./certbot/www:/var/www/certbot:ro"
fi
echo ""

# 5. Tester l'accès HTTP depuis le conteneur
echo -e "${BLUE}5️⃣  Test d'accès HTTP depuis le conteneur Nginx...${NC}"
TEST_FILE="certbot/www/.well-known/acme-challenge/test-$(date +%s).txt"
echo "test-content" > "$TEST_FILE"
chmod 644 "$TEST_FILE" 2>/dev/null || true

# Tester depuis l'intérieur du conteneur
if docker-compose exec -T nginx test -f /var/www/certbot/.well-known/acme-challenge/$(basename "$TEST_FILE") 2>/dev/null; then
    echo -e "${GREEN}✅ Fichier accessible depuis le conteneur${NC}"
else
    echo -e "${RED}❌ Fichier non accessible depuis le conteneur${NC}"
    echo "   Vérifiez le montage du volume"
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
docker-compose --profile production restart nginx
sleep 3
echo -e "${GREEN}✅ Nginx redémarré${NC}"
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
echo "   echo 'test' > certbot/www/.well-known/acme-challenge/test.txt"
echo "   curl http://$DOMAIN/.well-known/acme-challenge/test.txt"
echo ""
echo "4. Si tout est OK, relancez setup-ssl.sh:"
echo "   ./setup-ssl.sh"
echo ""
