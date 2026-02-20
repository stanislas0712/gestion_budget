#!/bin/bash
# Script pour résoudre l'erreur 'ContainerConfig' de Docker Compose

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Résolution de l'erreur 'ContainerConfig' de Docker Compose${NC}"
echo ""

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Étape 1: Arrêter tous les conteneurs
echo -e "${BLUE}📦 Étape 1: Arrêt de tous les conteneurs...${NC}"
docker-compose --profile production down 2>/dev/null || true
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✅ Conteneurs arrêtés${NC}"
echo ""

# Étape 2: Supprimer les conteneurs problématiques
echo -e "${BLUE}🗑️  Étape 2: Suppression des conteneurs problématiques...${NC}"
# Supprimer tous les conteneurs arrêtés
docker container prune -f 2>/dev/null || true

# Supprimer spécifiquement les conteneurs du projet
docker ps -a --filter "name=budget_" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true
echo -e "${GREEN}✅ Conteneurs supprimés${NC}"
echo ""

# Étape 3: Nettoyer les volumes orphelins
echo -e "${BLUE}🧹 Étape 3: Nettoyage des volumes...${NC}"
docker volume prune -f 2>/dev/null || true
echo -e "${GREEN}✅ Volumes nettoyés${NC}"
echo ""

# Étape 4: Supprimer les images corrompues (optionnel)
read -p "Voulez-vous supprimer et reconstruire les images? (o/N): " rebuild_images

if [[ $rebuild_images =~ ^[OoYy]$ ]]; then
    echo -e "${BLUE}🔄 Étape 4: Reconstruction des images...${NC}"
    # Supprimer les images du projet
    docker images --filter "reference=*budget*" --format "{{.ID}}" | xargs -r docker rmi -f 2>/dev/null || true
    
    # Reconstruire les images
    docker-compose --profile production build --no-cache
    echo -e "${GREEN}✅ Images reconstruites${NC}"
else
    echo -e "${YELLOW}⏭️  Reconstruction des images ignorée${NC}"
fi
echo ""

# Étape 5: Nettoyer le cache Docker (optionnel)
read -p "Voulez-vous nettoyer le cache Docker? (o/N): " clean_cache

if [[ $clean_cache =~ ^[OoYy]$ ]]; then
    echo -e "${BLUE}🧹 Étape 5: Nettoyage du cache Docker...${NC}"
    docker system prune -a -f --volumes
    echo -e "${GREEN}✅ Cache nettoyé${NC}"
else
    echo -e "${YELLOW}⏭️  Nettoyage du cache ignoré${NC}"
fi
echo ""

# Étape 6: Vérifier la configuration Docker Compose
echo -e "${BLUE}✅ Étape 6: Vérification de la configuration...${NC}"
if docker-compose --profile production config > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Configuration Docker Compose valide${NC}"
else
    echo -e "${RED}❌ Erreur dans la configuration Docker Compose${NC}"
    echo "   Vérifiez le fichier docker-compose.yml"
    docker-compose --profile production config
    exit 1
fi
echo ""

# Étape 7: Redémarrer les services
echo -e "${BLUE}🚀 Étape 7: Redémarrage des services...${NC}"
echo "   Cette étape peut prendre quelques minutes..."
docker-compose --profile production up -d

echo ""
echo -e "${GREEN}✅ Correction terminée!${NC}"
echo ""
echo "📋 Vérification du statut des conteneurs:"
docker-compose --profile production ps

echo ""
echo "📋 Logs des services:"
echo "   docker-compose --profile production logs -f"
