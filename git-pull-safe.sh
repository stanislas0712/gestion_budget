#!/bin/bash
# Script pour faire un pull Git en sécurité avec gestion des conflits

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Vérification des modifications locales...${NC}"

# Vérifier s'il y a des modifications
if git diff --quiet && git diff --cached --quiet; then
    echo -e "${GREEN}✅ Aucune modification locale, pull direct...${NC}"
    git pull
    echo -e "${GREEN}✅ Pull terminé avec succès${NC}"
else
    echo -e "${YELLOW}⚠️  Modifications locales détectées${NC}"
    echo ""
    git status --short
    echo ""
    echo -e "${BLUE}Options:${NC}"
    echo "  1. Stash les modifications puis pull (recommandé)"
    echo "  2. Commiter les modifications puis pull"
    echo "  3. Écraser les modifications locales (ATTENTION: perte de données)"
    echo "  4. Annuler"
    echo ""
    read -p "Choix (1-4): " choice
    
    case $choice in
        1)
            echo -e "${BLUE}📦 Sauvegarde des modifications...${NC}"
            git stash
            echo -e "${GREEN}✅ Modifications sauvegardées${NC}"
            
            echo -e "${BLUE}⬇️  Pull depuis le dépôt distant...${NC}"
            git pull
            
            echo -e "${BLUE}📥 Récupération des modifications...${NC}"
            if git stash pop; then
                echo -e "${GREEN}✅ Pull terminé, modifications récupérées${NC}"
            else
                echo -e "${YELLOW}⚠️  Conflits détectés lors de la récupération${NC}"
                echo "   Résolvez les conflits manuellement puis:"
                echo "   git add . && git commit -m 'Résolution conflits'"
            fi
            ;;
        2)
            echo -e "${BLUE}📝 Préparation du commit...${NC}"
            git add .
            
            read -p "Message de commit: " msg
            if [ -z "$msg" ]; then
                msg="Mise à jour avant pull"
            fi
            
            git commit -m "$msg"
            echo -e "${GREEN}✅ Modifications commitées${NC}"
            
            echo -e "${BLUE}⬇️  Pull depuis le dépôt distant...${NC}"
            if git pull; then
                echo -e "${GREEN}✅ Pull terminé avec succès${NC}"
            else
                echo -e "${YELLOW}⚠️  Conflits détectés${NC}"
                echo "   Résolvez les conflits puis:"
                echo "   git add . && git commit -m 'Résolution conflits'"
            fi
            ;;
        3)
            echo -e "${RED}⚠️  ATTENTION: Cette opération va écraser toutes les modifications locales!${NC}"
            read -p "Êtes-vous sûr? (oui/non): " confirm
            if [[ "$confirm" =~ ^[Oo][Uu][Ii]$ ]]; then
                echo -e "${BLUE}🔄 Réinitialisation...${NC}"
                git reset --hard origin/main
                echo -e "${BLUE}⬇️  Pull depuis le dépôt distant...${NC}"
                git pull
                echo -e "${GREEN}✅ Pull terminé, modifications locales écrasées${NC}"
            else
                echo -e "${YELLOW}❌ Opération annulée${NC}"
                exit 1
            fi
            ;;
        4)
            echo -e "${YELLOW}❌ Opération annulée${NC}"
            exit 1
            ;;
        *)
            echo -e "${RED}❌ Choix invalide${NC}"
            exit 1
            ;;
    esac
fi
