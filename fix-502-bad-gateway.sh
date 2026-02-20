#!/bin/bash
# Script pour diagnostiquer et corriger l'erreur 502 Bad Gateway

set +e  # Ne pas arrêter sur toutes les erreurs

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Diagnostic et correction de l'erreur 502 Bad Gateway${NC}"
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

WEB_PORT="${WEB_PORT:-8000}"

echo -e "${BLUE}📋 Configuration:${NC}"
echo "   Port Django: $WEB_PORT"
echo ""

# 1. Vérifier si Docker est démarré
echo -e "${BLUE}1️⃣  Vérification de Docker...${NC}"
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker n'est pas accessible${NC}"
    echo "   Démarrez Docker: sudo systemctl start docker"
    exit 1
fi
echo -e "${GREEN}✅ Docker est accessible${NC}"
echo ""

# 2. Vérifier si le conteneur Django est démarré
echo -e "${BLUE}2️⃣  Vérification du conteneur Django...${NC}"
if docker ps --filter "name=budget_web" --format "{{.Names}}" | grep -q "budget_web"; then
    echo -e "${GREEN}✅ Conteneur Django est démarré${NC}"
    CONTAINER_STATUS=$(docker ps --filter "name=budget_web" --format "{{.Status}}")
    echo "   Statut: $CONTAINER_STATUS"
else
    echo -e "${RED}❌ Conteneur Django n'est pas démarré${NC}"
    echo "   Démarrage du conteneur..."
    if docker-compose --profile production up -d web; then
        echo -e "${GREEN}✅ Conteneur Django démarré${NC}"
        echo "   Attente de 10 secondes pour que Django soit prêt..."
        sleep 10
    else
        echo -e "${RED}❌ Erreur lors du démarrage du conteneur${NC}"
        echo "   Vérifiez les logs: docker-compose logs web"
        exit 1
    fi
fi
echo ""

# 3. Vérifier si Django répond sur le port 8000
echo -e "${BLUE}3️⃣  Vérification de l'accessibilité de Django sur le port $WEB_PORT...${NC}"
if curl -f -s -o /dev/null -w "%{http_code}" "http://localhost:$WEB_PORT/" > /tmp/curl_output.txt 2>&1; then
    HTTP_CODE=$(cat /tmp/curl_output.txt)
    echo -e "${GREEN}✅ Django répond sur le port $WEB_PORT (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}❌ Django ne répond pas sur le port $WEB_PORT${NC}"
    echo "   Erreur: $(cat /tmp/curl_output.txt 2>/dev/null || echo 'Connection refused')"
    echo ""
    echo "   Vérifications:"
    echo "   - Vérifiez les logs Django: docker-compose logs web"
    echo "   - Vérifiez que le port est exposé: docker ps | grep budget_web"
    echo "   - Testez depuis le conteneur: docker exec budget_web curl http://localhost:8000/"
    echo ""
    read -p "Voulez-vous voir les logs Django? (O/n): " see_logs
    see_logs=${see_logs:-O}
    if [[ $see_logs =~ ^[OoYy]$ ]]; then
        echo ""
        echo "📋 Dernières lignes des logs Django:"
        docker-compose logs --tail=50 web
    fi
    exit 1
fi
echo ""

# 4. Vérifier la configuration Nginx
echo -e "${BLUE}4️⃣  Vérification de la configuration Nginx...${NC}"
NGINX_SITE="/etc/nginx/sites-available/budget.bkdb.bf"
if [ ! -f "$NGINX_SITE" ]; then
    echo -e "${RED}❌ Configuration Nginx non trouvée: $NGINX_SITE${NC}"
    echo "   Créez-la avec: ./configure-nginx.sh"
    exit 1
fi

# Vérifier que Nginx pointe vers le bon port
if sudo grep -q "proxy_pass http://localhost:$WEB_PORT" "$NGINX_SITE" 2>/dev/null; then
    echo -e "${GREEN}✅ Nginx pointe vers le bon port ($WEB_PORT)${NC}"
else
    echo -e "${YELLOW}⚠️  Nginx ne pointe pas vers le port $WEB_PORT${NC}"
    echo "   Configuration actuelle:"
    sudo grep "proxy_pass" "$NGINX_SITE" | head -1
    echo ""
    read -p "Voulez-vous corriger la configuration Nginx? (O/n): " fix_nginx
    fix_nginx=${fix_nginx:-O}
    if [[ $fix_nginx =~ ^[OoYy]$ ]]; then
        echo "   Correction de la configuration Nginx..."
        # Remplacer le port dans la configuration
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sudo sed -i '' "s|proxy_pass http://localhost:[0-9]*;|proxy_pass http://localhost:$WEB_PORT;|g" "$NGINX_SITE"
        else
            sudo sed -i "s|proxy_pass http://localhost:[0-9]*;|proxy_pass http://localhost:$WEB_PORT;|g" "$NGINX_SITE"
        fi
        echo -e "${GREEN}✅ Configuration Nginx corrigée${NC}"
        
        # Tester la configuration
        if sudo nginx -t; then
            echo -e "${GREEN}✅ Configuration Nginx valide${NC}"
            sudo systemctl reload nginx
            echo -e "${GREEN}✅ Nginx rechargé${NC}"
        else
            echo -e "${RED}❌ Erreur dans la configuration Nginx${NC}"
            sudo nginx -t
            exit 1
        fi
    fi
fi
echo ""

# 5. Vérifier que Nginx est démarré
echo -e "${BLUE}5️⃣  Vérification de Nginx...${NC}"
if sudo systemctl is-active --quiet nginx 2>/dev/null; then
    echo -e "${GREEN}✅ Nginx est démarré${NC}"
else
    echo -e "${RED}❌ Nginx n'est pas démarré${NC}"
    echo "   Démarrage de Nginx..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
    sleep 2
    if sudo systemctl is-active --quiet nginx; then
        echo -e "${GREEN}✅ Nginx démarré${NC}"
    else
        echo -e "${RED}❌ Erreur lors du démarrage de Nginx${NC}"
        echo "   Vérifiez les logs: sudo journalctl -u nginx -n 50"
        exit 1
    fi
fi
echo ""

# 6. Test final
echo -e "${BLUE}6️⃣  Test final de connectivité...${NC}"
echo "   Test depuis Nginx vers Django..."
if curl -f -s -o /dev/null "http://localhost:$WEB_PORT/" 2>/dev/null; then
    echo -e "${GREEN}✅ Django est accessible depuis l'hôte${NC}"
else
    echo -e "${YELLOW}⚠️  Django n'est pas accessible depuis l'hôte${NC}"
    echo "   Cela peut être normal si le port n'est pas exposé sur l'hôte"
    echo "   Vérifiez que docker-compose.yml expose le port: ports: - \"8000:8000\""
fi

# Vérifier les logs Nginx pour les erreurs récentes
echo ""
echo -e "${BLUE}📋 Dernières erreurs Nginx (si disponibles):${NC}"
if [ -f "/var/log/nginx/budget-error.log" ]; then
    sudo tail -5 /var/log/nginx/budget-error.log 2>/dev/null || echo "   Aucune erreur récente"
elif [ -f "/var/log/nginx/error.log" ]; then
    sudo tail -5 /var/log/nginx/error.log 2>/dev/null | grep -i "502\|bad gateway\|upstream" || echo "   Aucune erreur 502 récente"
else
    echo "   Fichier de log non trouvé"
fi
echo ""

echo -e "${GREEN}✅ Diagnostic terminé!${NC}"
echo ""
echo -e "${YELLOW}📝 Résumé:${NC}"
echo "1. Conteneur Django: $(docker ps --filter "name=budget_web" --format "{{.Status}}" 2>/dev/null || echo 'Non démarré')"
echo "2. Port $WEB_PORT: $(curl -f -s -o /dev/null -w "%{http_code}" "http://localhost:$WEB_PORT/" 2>/dev/null && echo 'Accessible' || echo 'Non accessible')"
echo "3. Nginx: $(sudo systemctl is-active nginx 2>/dev/null && echo 'Actif' || echo 'Inactif')"
echo ""
echo -e "${BLUE}💡 Commandes utiles:${NC}"
echo "   - Voir les logs Django: docker-compose logs -f web"
echo "   - Voir les logs Nginx: sudo tail -f /var/log/nginx/budget-error.log"
echo "   - Redémarrer Django: docker-compose restart web"
echo "   - Redémarrer Nginx: sudo systemctl restart nginx"
echo ""
