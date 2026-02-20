#!/bin/bash
# Script pour corriger les erreurs CSRF en production

set +e  # Ne pas arrêter sur toutes les erreurs

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Correction des erreurs CSRF en production${NC}"
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
echo "   DJANGO_USE_SSL: ${DJANGO_USE_SSL:-non défini}"
echo ""

# Vérifier le fichier .env
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Fichier .env non trouvé${NC}"
    echo "   Créez-le depuis env.example: cp env.example .env"
    exit 1
fi

# Vérifier et mettre à jour DJANGO_USE_SSL
CURRENT_USE_SSL=$(grep "^DJANGO_USE_SSL=" .env 2>/dev/null | cut -d'=' -f2- || echo "")

if [ -z "$CURRENT_USE_SSL" ]; then
    echo -e "${YELLOW}⚠️  DJANGO_USE_SSL non trouvé dans .env${NC}"
    echo "   Ajout de DJANGO_USE_SSL=true..."
    echo "DJANGO_USE_SSL=true" >> .env
    echo -e "${GREEN}✅ DJANGO_USE_SSL ajouté${NC}"
elif [ "$CURRENT_USE_SSL" != "true" ]; then
    echo -e "${YELLOW}⚠️  DJANGO_USE_SSL=$CURRENT_USE_SSL (devrait être 'true' en production avec SSL)${NC}"
    read -p "Voulez-vous mettre à jour DJANGO_USE_SSL à 'true'? (O/n): " update_ssl
    update_ssl=${update_ssl:-O}
    
    if [[ $update_ssl =~ ^[OoYy]$ ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^DJANGO_USE_SSL=.*|DJANGO_USE_SSL=true|" .env
        else
            sed -i "s|^DJANGO_USE_SSL=.*|DJANGO_USE_SSL=true|" .env
        fi
        echo -e "${GREEN}✅ DJANGO_USE_SSL mis à jour à 'true'${NC}"
    fi
else
    echo -e "${GREEN}✅ DJANGO_USE_SSL est déjà configuré à 'true'${NC}"
fi

echo ""
echo -e "${BLUE}📋 Vérification de la configuration Nginx...${NC}"

# Vérifier que Nginx transmet correctement les headers
NGINX_SITE="/etc/nginx/sites-available/budget.bkdb.bf"
if [ -f "$NGINX_SITE" ]; then
    if sudo grep -q "proxy_set_header X-Forwarded-Proto" "$NGINX_SITE" 2>/dev/null; then
        echo -e "${GREEN}✅ Nginx transmet X-Forwarded-Proto${NC}"
    else
        echo -e "${RED}❌ Nginx ne transmet pas X-Forwarded-Proto${NC}"
        echo "   Ajoutez dans la configuration Nginx:"
        echo "   proxy_set_header X-Forwarded-Proto \$scheme;"
    fi
    
    if sudo grep -q "proxy_set_header Host" "$NGINX_SITE" 2>/dev/null; then
        echo -e "${GREEN}✅ Nginx transmet le header Host${NC}"
    else
        echo -e "${RED}❌ Nginx ne transmet pas le header Host${NC}"
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

# Redémarrer Nginx si nécessaire
if sudo systemctl is-active --quiet nginx 2>/dev/null; then
    echo "   Rechargement de Nginx..."
    sudo systemctl reload nginx
    echo -e "${GREEN}✅ Nginx rechargé${NC}"
fi

echo ""
echo -e "${GREEN}✅ Correction terminée!${NC}"
echo ""
echo -e "${YELLOW}📝 Vérifications:${NC}"
echo "1. Vérifiez que .env contient:"
echo "   DJANGO_USE_SSL=true"
echo "   DOMAIN_NAME=$DOMAIN"
echo ""
echo "2. Vérifiez que Nginx transmet les headers:"
echo "   sudo grep 'X-Forwarded-Proto' $NGINX_SITE"
echo "   sudo grep 'proxy_set_header Host' $NGINX_SITE"
echo ""
echo "3. Vérifiez les logs Django pour les erreurs CSRF:"
echo "   docker-compose logs web | grep -i csrf"
echo ""
echo -e "${BLUE}💡 Note:${NC}"
echo "   - CSRF_TRUSTED_ORIGINS est maintenant configuré automatiquement dans prod.py"
echo "   - Les cookies CSRF sont sécurisés si DJANGO_USE_SSL=true"
echo "   - Assurez-vous que Nginx transmet X-Forwarded-Proto correctement"
echo ""
