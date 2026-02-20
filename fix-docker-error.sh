#!/bin/bash
# Script pour résoudre l'erreur 'ContainerConfig' de Docker Compose

# Ne pas utiliser set -e au début pour permettre l'interruption
# On l'activera seulement pour les étapes critiques

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Gestion de l'interruption (Ctrl+C)
cleanup() {
    echo ""
    echo -e "${YELLOW}⚠️  Interruption détectée. Nettoyage en cours...${NC}"
    # Arrêter les opérations en cours si nécessaire
    exit 130
}

trap cleanup INT TERM

echo -e "${BLUE}🔧 Résolution de l'erreur 'ContainerConfig' de Docker Compose${NC}"
echo -e "${YELLOW}💡 Appuyez sur Ctrl+C à tout moment pour interrompre${NC}"
echo ""

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Étape 1: Arrêter tous les conteneurs
echo -e "${BLUE}📦 Étape 1: Arrêt de tous les conteneurs...${NC}"
if docker-compose --profile production down 2>/dev/null; then
    echo "   Production arrêté"
elif docker-compose down 2>/dev/null; then
    echo "   Services arrêtés"
else
    echo "   Aucun conteneur à arrêter"
fi
echo -e "${GREEN}✅ Conteneurs arrêtés${NC}"
echo ""

# Étape 2: Supprimer les conteneurs problématiques
echo -e "${BLUE}🗑️  Étape 2: Suppression des conteneurs problématiques...${NC}"
# Supprimer tous les conteneurs arrêtés
if docker container prune -f 2>/dev/null; then
    echo "   Conteneurs orphelins supprimés"
fi

# Supprimer spécifiquement les conteneurs du projet
CONTAINER_IDS=$(docker ps -a --filter "name=budget_" --format "{{.ID}}" 2>/dev/null || true)
if [ -n "$CONTAINER_IDS" ]; then
    echo "$CONTAINER_IDS" | while read -r id; do
        if [ -n "$id" ]; then
            docker rm -f "$id" 2>/dev/null && echo "   Conteneur $id supprimé" || true
        fi
    done
else
    echo "   Aucun conteneur budget_ à supprimer"
fi
echo -e "${GREEN}✅ Conteneurs supprimés${NC}"
echo ""

# Étape 3: Nettoyer les volumes orphelins
echo -e "${BLUE}🧹 Étape 3: Nettoyage des volumes...${NC}"
if docker volume prune -f 2>/dev/null; then
    echo -e "${GREEN}✅ Volumes nettoyés${NC}"
else
    echo "   Aucun volume orphelin à nettoyer"
fi
echo ""

# Étape 4: Supprimer les images corrompues (optionnel)
echo -e "${YELLOW}💡 Appuyez sur Ctrl+C pour annuler à tout moment${NC}"
read -p "Voulez-vous supprimer et reconstruire les images? (o/N): " rebuild_images

if [[ $rebuild_images =~ ^[OoYy]$ ]]; then
    echo -e "${BLUE}🔄 Étape 4: Reconstruction des images...${NC}"
    # Supprimer les images du projet
    IMAGE_IDS=$(docker images --filter "reference=*budget*" --format "{{.ID}}" 2>/dev/null || true)
    if [ -n "$IMAGE_IDS" ]; then
        echo "$IMAGE_IDS" | while read -r id; do
            if [ -n "$id" ]; then
                docker rmi -f "$id" 2>/dev/null && echo "   Image $id supprimée" || true
            fi
        done
    fi
    
    # Reconstruire les images (peut prendre du temps, mais peut être interrompu)
    echo "   Reconstruction en cours (peut prendre plusieurs minutes)..."
    if docker-compose --profile production build --no-cache; then
        echo -e "${GREEN}✅ Images reconstruites${NC}"
    else
        echo -e "${RED}❌ Erreur lors de la reconstruction${NC}"
        echo "   Vous pouvez continuer ou réessayer plus tard"
    fi
else
    echo -e "${YELLOW}⏭️  Reconstruction des images ignorée${NC}"
fi
echo ""

# Étape 5: Nettoyer le cache Docker (optionnel)
echo -e "${YELLOW}⚠️  ATTENTION: Le nettoyage du cache supprimera toutes les images non utilisées${NC}"
read -p "Voulez-vous nettoyer le cache Docker? (o/N): " clean_cache

if [[ $clean_cache =~ ^[OoYy]$ ]]; then
    echo -e "${BLUE}🧹 Étape 5: Nettoyage du cache Docker...${NC}"
    echo "   Cette opération peut prendre du temps..."
    if docker system prune -a -f --volumes; then
        echo -e "${GREEN}✅ Cache nettoyé${NC}"
    else
        echo -e "${YELLOW}⚠️  Erreur lors du nettoyage (peut être normal)${NC}"
    fi
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
    docker-compose --profile production config 2>&1 | head -20
    echo ""
    echo -e "${YELLOW}⚠️  Le script s'arrête ici. Corrigez les erreurs puis relancez.${NC}"
    exit 1
fi
echo ""

# Étape 7: Redémarrer les services
echo -e "${BLUE}🚀 Étape 7: Redémarrage des services...${NC}"
echo "   Cette étape peut prendre quelques minutes..."
echo -e "${YELLOW}💡 Vous pouvez interrompre avec Ctrl+C si nécessaire${NC}"
echo ""

if docker-compose --profile production up -d; then
    echo ""
    echo -e "${GREEN}✅ Correction terminée!${NC}"
    echo ""
    echo "📋 Vérification du statut des conteneurs:"
    docker-compose --profile production ps 2>/dev/null || docker-compose ps
    
    echo ""
    echo "📋 Commandes utiles:"
    echo "   Voir les logs: docker-compose --profile production logs -f"
    echo "   Voir le statut: docker-compose --profile production ps"
    echo "   Arrêter: docker-compose --profile production down"
else
    echo ""
    echo -e "${RED}❌ Erreur lors du démarrage des services${NC}"
    echo "   Vérifiez les logs avec: docker-compose --profile production logs"
    exit 1
fi
