#!/bin/bash
# Script pour corriger les erreurs ALLOWED_HOSTS de Django

set +e  # Ne pas arrêter sur toutes les erreurs

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Correction des erreurs ALLOWED_HOSTS de Django${NC}"
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

echo -e "${BLUE}📋 Configuration actuelle:${NC}"
echo "   Domaine: $DOMAIN"
echo "   ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS:-non défini}"
echo ""

# Obtenir l'IP du serveur
echo -e "${BLUE}🔍 Détection de l'IP du serveur...${NC}"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || hostname -I | awk '{print $1}' || echo "")
if [ -n "$SERVER_IP" ]; then
    echo "   IP du serveur: $SERVER_IP"
else
    echo -e "${YELLOW}⚠️  Impossible de détecter l'IP du serveur${NC}"
fi
echo ""

# Construire la liste des hôtes à ajouter
HOSTS_TO_ADD="$DOMAIN,www.$DOMAIN,localhost,127.0.0.1,0.0.0.0"
if [ -n "$SERVER_IP" ]; then
    HOSTS_TO_ADD="$HOSTS_TO_ADD,$SERVER_IP"
    # Ajouter aussi SERVER_IP dans .env pour que Django l'utilise
    if ! grep -q "^SERVER_IP=" .env 2>/dev/null; then
        echo "SERVER_IP=$SERVER_IP" >> .env
        echo -e "${GREEN}✅ SERVER_IP ajouté dans .env${NC}"
    elif ! grep -q "^SERVER_IP=$SERVER_IP" .env 2>/dev/null; then
        # Mettre à jour si différent
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^SERVER_IP=.*|SERVER_IP=$SERVER_IP|" .env
        else
            sed -i "s|^SERVER_IP=.*|SERVER_IP=$SERVER_IP|" .env
        fi
        echo -e "${GREEN}✅ SERVER_IP mis à jour dans .env${NC}"
    fi
fi

# Vérifier le fichier .env
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Fichier .env non trouvé${NC}"
    echo "   Créez-le depuis env.example: cp env.example .env"
    exit 1
fi

# Vérifier si DJANGO_ALLOWED_HOSTS existe
CURRENT_HOSTS=$(grep "^DJANGO_ALLOWED_HOSTS=" .env 2>/dev/null | cut -d'=' -f2- || echo "")

if [ -z "$CURRENT_HOSTS" ]; then
    echo -e "${YELLOW}⚠️  DJANGO_ALLOWED_HOSTS non trouvé dans .env${NC}"
    echo "   Ajout de la ligne..."
    echo "DJANGO_ALLOWED_HOSTS=$HOSTS_TO_ADD" >> .env
    echo -e "${GREEN}✅ DJANGO_ALLOWED_HOSTS ajouté${NC}"
else
    echo -e "${BLUE}📝 DJANGO_ALLOWED_HOSTS actuel: $CURRENT_HOSTS${NC}"
    
    # Vérifier si le domaine est déjà présent
    if echo "$CURRENT_HOSTS" | grep -q "$DOMAIN"; then
        echo -e "${GREEN}✅ Le domaine $DOMAIN est déjà dans ALLOWED_HOSTS${NC}"
    else
        echo -e "${YELLOW}⚠️  Le domaine $DOMAIN n'est pas dans ALLOWED_HOSTS${NC}"
        read -p "Voulez-vous mettre à jour DJANGO_ALLOWED_HOSTS? (O/n): " update_hosts
        update_hosts=${update_hosts:-O}
        
        if [[ $update_hosts =~ ^[OoYy]$ ]]; then
            # Mettre à jour la ligne
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s|^DJANGO_ALLOWED_HOSTS=.*|DJANGO_ALLOWED_HOSTS=$HOSTS_TO_ADD|" .env
            else
                # Linux
                sed -i "s|^DJANGO_ALLOWED_HOSTS=.*|DJANGO_ALLOWED_HOSTS=$HOSTS_TO_ADD|" .env
            fi
            echo -e "${GREEN}✅ DJANGO_ALLOWED_HOSTS mis à jour${NC}"
        fi
    fi
fi

echo ""
echo -e "${BLUE}📋 Vérification de la configuration Nginx...${NC}"

# Vérifier que Nginx envoie le bon header Host
NGINX_SITE="/etc/nginx/sites-available/budget.bkdb.bf"
if [ -f "$NGINX_SITE" ]; then
    if sudo grep -q "proxy_set_header Host" "$NGINX_SITE" 2>/dev/null; then
        # Vérifier que c'est bien $host et pas localhost:8000
        if sudo grep -q "proxy_set_header Host.*localhost" "$NGINX_SITE" 2>/dev/null; then
            echo -e "${RED}❌ Nginx envoie localhost dans le header Host${NC}"
            echo "   Correction nécessaire dans $NGINX_SITE"
            echo "   Utilisez: proxy_set_header Host \$host;"
        else
            echo -e "${GREEN}✅ Nginx configure correctement le header Host${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Header Host non trouvé dans la configuration Nginx${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Configuration Nginx non trouvée: $NGINX_SITE${NC}"
fi

echo ""
echo -e "${BLUE}🔄 Redémarrage des services...${NC}"

# Redémarrer Django (Docker)
if docker-compose ps web 2>/dev/null | grep -q "Up"; then
    echo "   Redémarrage du service web Django..."
    docker-compose restart web
    sleep 3
    echo -e "${GREEN}✅ Service web redémarré${NC}"
else
    echo -e "${YELLOW}⚠️  Service web Django non démarré${NC}"
    echo "   Démarrez avec: docker-compose --profile production up -d web"
fi

echo ""
echo -e "${GREEN}✅ Correction terminée!${NC}"
echo ""
echo -e "${YELLOW}📝 Vérifications:${NC}"
echo "1. Vérifiez que .env contient:"
echo "   DJANGO_ALLOWED_HOSTS=$HOSTS_TO_ADD"
echo ""
echo "2. Vérifiez que Nginx envoie le bon header Host:"
echo "   sudo grep 'proxy_set_header Host' $NGINX_SITE"
echo "   Doit afficher: proxy_set_header Host \$host;"
echo ""
echo "3. Redémarrez Django si nécessaire:"
echo "   docker-compose restart web"
echo ""
