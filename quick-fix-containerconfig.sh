#!/bin/bash
# Script rapide pour résoudre l'erreur ContainerConfig

set +e  # Ne pas arrêter sur toutes les erreurs

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Correction rapide de l'erreur ContainerConfig${NC}"
echo ""

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Arrêter tous les conteneurs
echo -e "${BLUE}1️⃣  Arrêt de tous les conteneurs...${NC}"
docker-compose --profile production down 2>/dev/null || true
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✅ Conteneurs arrêtés${NC}"
echo ""

# 2. Supprimer tous les conteneurs arrêtés
echo -e "${BLUE}2️⃣  Suppression de tous les conteneurs arrêtés...${NC}"
docker ps -a --filter "status=exited" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true
docker ps -a --filter "status=created" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true
docker container prune -f 2>/dev/null || true
echo -e "${GREEN}✅ Conteneurs supprimés${NC}"
echo ""

# 3. Supprimer les conteneurs du projet
echo -e "${BLUE}3️⃣  Suppression des conteneurs du projet...${NC}"
docker ps -a --filter "name=budget_" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true
echo -e "${GREEN}✅ Conteneurs du projet supprimés${NC}"
echo ""

# 4. Supprimer les images corrompues
echo -e "${BLUE}4️⃣  Suppression des images corrompues...${NC}"
docker images --filter "reference=*budget*" --format "{{.ID}}" | xargs -r docker rmi -f 2>/dev/null || true
docker image prune -f 2>/dev/null || true
echo -e "${GREEN}✅ Images supprimées${NC}"
echo ""

# 5. Reconstruire les images
echo -e "${BLUE}5️⃣  Reconstruction des images...${NC}"
echo "   Cela peut prendre plusieurs minutes..."
if docker-compose --profile production build --no-cache; then
    echo -e "${GREEN}✅ Images reconstruites${NC}"
else
    echo -e "${RED}❌ Erreur lors de la reconstruction${NC}"
    exit 1
fi
echo ""

# 6. Redémarrer les services
echo -e "${BLUE}6️⃣  Redémarrage des services...${NC}"
if docker-compose --profile production up -d; then
    echo -e "${GREEN}✅ Services redémarrés${NC}"
else
    echo -e "${RED}❌ Erreur lors du redémarrage${NC}"
    exit 1
fi
echo ""

echo -e "${GREEN}✅ Correction terminée!${NC}"
echo ""
echo "📋 Vérification du statut:"
docker-compose --profile production ps
