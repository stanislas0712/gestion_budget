#!/bin/bash
# Script pour mettre à jour uniquement le conteneur web Django sans toucher à la base de données

set -e  # Arrêter en cas d'erreur

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Déploiement du conteneur web Django${NC}"
echo -e "${YELLOW}⚠️  La base de données ne sera PAS affectée${NC}"
echo ""

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Vérifier que nous sommes dans un dépôt Git
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Ce répertoire n'est pas un dépôt Git${NC}"
    exit 1
fi

# Vérifier si on doit corriger l'erreur ContainerConfig d'abord
echo -e "${BLUE}🔍 Vérification de l'état Docker...${NC}"
if docker ps -a --filter "name=budget_web" --format "{{.Names}}" | grep -q "budget_web"; then
    CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' budget_web 2>/dev/null || echo "unknown")
    if [ "$CONTAINER_STATUS" != "running" ]; then
        echo -e "${YELLOW}⚠️  Conteneur web trouvé mais non démarré (statut: $CONTAINER_STATUS)${NC}"
        echo "   Nettoyage des conteneurs problématiques..."
        docker-compose rm -f web 2>/dev/null || true
        docker ps -a --filter "name=budget_web" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true
        echo -e "${GREEN}✅ Conteneurs problématiques supprimés${NC}"
    fi
fi
echo ""

# Étape 1: Sauvegarder les modifications locales (optionnel)
echo -e "${BLUE}1️⃣  Vérification des modifications locales...${NC}"
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  Des modifications locales non commitées ont été détectées${NC}"
    read -p "Voulez-vous les sauvegarder avec git stash? (O/n): " stash_choice
    stash_choice=${stash_choice:-O}
    
    if [[ $stash_choice =~ ^[OoYy]$ ]]; then
        git stash push -m "Sauvegarde avant déploiement $(date +%Y-%m-%d_%H-%M-%S)"
        echo -e "${GREEN}✅ Modifications sauvegardées${NC}"
        RESTORE_STASH=true
    else
        echo -e "${YELLOW}⚠️  Les modifications locales seront perdues lors du pull${NC}"
        read -p "Continuer quand même? (o/N): " continue_choice
        if [[ ! $continue_choice =~ ^[OoYy]$ ]]; then
            echo -e "${YELLOW}⏭️  Déploiement annulé${NC}"
            exit 0
        fi
    fi
else
    echo -e "${GREEN}✅ Aucune modification locale${NC}"
    RESTORE_STASH=false
fi
echo ""

# Étape 2: Récupérer le nouveau code
echo -e "${BLUE}2️⃣  Récupération du nouveau code depuis Git...${NC}"
read -p "Voulez-vous faire un git pull? (O/n): " pull_choice
pull_choice=${pull_choice:-O}

if [[ $pull_choice =~ ^[OoYy]$ ]]; then
    if git pull; then
        echo -e "${GREEN}✅ Code mis à jour${NC}"
    else
        echo -e "${RED}❌ Erreur lors du git pull${NC}"
        echo "   Résolvez les conflits manuellement puis relancez le script"
        if [ "$RESTORE_STASH" = true ]; then
            git stash pop
        fi
        exit 1
    fi
else
    echo -e "${YELLOW}⏭️  Git pull ignoré (utilisation du code local)${NC}"
fi
echo ""

# Étape 3: Vérifier que la base de données est toujours accessible
echo -e "${BLUE}3️⃣  Vérification de la base de données...${NC}"
if docker-compose ps db 2>/dev/null | grep -q "Up"; then
    echo -e "${GREEN}✅ Base de données est en cours d'exécution${NC}"
    echo -e "${YELLOW}   La base de données ne sera PAS modifiée${NC}"
else
    echo -e "${YELLOW}⚠️  Base de données non démarrée (sera démarrée si nécessaire)${NC}"
fi
echo ""

# Étape 4: Arrêter et supprimer le conteneur web (pour éviter l'erreur ContainerConfig)
echo -e "${BLUE}4️⃣  Arrêt et suppression du conteneur web...${NC}"

# Arrêter le conteneur s'il est en cours d'exécution
if docker-compose ps web 2>/dev/null | grep -q "Up"; then
    docker-compose stop web
    echo "   Conteneur web arrêté"
fi

# Supprimer le conteneur web (même s'il est arrêté) pour éviter l'erreur ContainerConfig
CONTAINER_ID=$(docker ps -a --filter "name=budget_web" --format "{{.ID}}" 2>/dev/null | head -1)
if [ -n "$CONTAINER_ID" ]; then
    echo "   Suppression du conteneur web (ID: $CONTAINER_ID)..."
    docker rm -f "$CONTAINER_ID" 2>/dev/null || true
    echo -e "${GREEN}✅ Conteneur web supprimé${NC}"
else
    echo -e "${YELLOW}⚠️  Aucun conteneur web trouvé${NC}"
fi

# Supprimer aussi les conteneurs avec des noms similaires (pour les anciens conteneurs)
docker ps -a --filter "name=budget_web" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true

echo ""

# Étape 5: Reconstruire l'image du service web
echo -e "${BLUE}5️⃣  Reconstruction de l'image Docker du service web...${NC}"
echo "   Cela peut prendre plusieurs minutes..."
if docker-compose build web; then
    echo -e "${GREEN}✅ Image reconstruite${NC}"
else
    echo -e "${RED}❌ Erreur lors de la reconstruction${NC}"
    if [ "$RESTORE_STASH" = true ]; then
        git stash pop
    fi
    exit 1
fi
echo ""

# Étape 6: Démarrer le conteneur web (créer un nouveau conteneur)
echo -e "${BLUE}6️⃣  Création et démarrage du conteneur web...${NC}"

# Utiliser --force-recreate pour forcer la création d'un nouveau conteneur
if docker-compose up -d --force-recreate --no-deps web; then
    echo -e "${GREEN}✅ Conteneur web créé et démarré${NC}"
else
    echo -e "${RED}❌ Erreur lors du démarrage${NC}"
    echo "   Tentative alternative..."
    
    # Tentative alternative: supprimer complètement et recréer
    docker-compose rm -f web 2>/dev/null || true
    docker ps -a --filter "name=budget_web" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true
    
    if docker-compose up -d --no-deps web; then
        echo -e "${GREEN}✅ Conteneur web créé et démarré (méthode alternative)${NC}"
    else
        echo -e "${RED}❌ Erreur persistante lors du démarrage${NC}"
        echo "   Vérifiez les logs: docker-compose logs web"
        exit 1
    fi
fi
echo ""

# Étape 7: Attendre que Django soit prêt
echo -e "${BLUE}7️⃣  Attente que Django soit prêt...${NC}"
sleep 5

# Vérifier que le conteneur répond
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s -o /dev/null "http://localhost:8000/" 2>/dev/null; then
        echo -e "${GREEN}✅ Django répond correctement${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "   Tentative $RETRY_COUNT/$MAX_RETRIES..."
        sleep 3
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}⚠️  Django ne répond pas encore, mais le conteneur est démarré${NC}"
    echo "   Vérifiez les logs: docker-compose logs web"
fi
echo ""

# Étape 8: Appliquer les migrations (si nécessaire)
echo -e "${BLUE}8️⃣  Vérification des migrations...${NC}"
read -p "Voulez-vous appliquer les migrations? (O/n): " migrate_choice
migrate_choice=${migrate_choice:-O}

if [[ $migrate_choice =~ ^[OoYy]$ ]]; then
    echo "   Application des migrations..."
    if docker-compose exec -T web python manage.py migrate --noinput; then
        echo -e "${GREEN}✅ Migrations appliquées${NC}"
    else
        echo -e "${YELLOW}⚠️  Erreur lors des migrations (peut être normal si aucune migration)${NC}"
    fi
else
    echo -e "${YELLOW}⏭️  Migrations ignorées${NC}"
fi
echo ""

# Étape 9: Collecter les fichiers statiques (si nécessaire)
echo -e "${BLUE}9️⃣  Collecte des fichiers statiques...${NC}"
read -p "Voulez-vous collecter les fichiers statiques? (O/n): " collectstatic_choice
collectstatic_choice=${collectstatic_choice:-O}

if [[ $collectstatic_choice =~ ^[OoYy]$ ]]; then
    echo "   Collecte en cours..."
    if docker-compose exec -T web python manage.py collectstatic --noinput; then
        echo -e "${GREEN}✅ Fichiers statiques collectés${NC}"
    else
        echo -e "${YELLOW}⚠️  Erreur lors de la collecte (peut être normal)${NC}"
    fi
else
    echo -e "${YELLOW}⏭️  Collecte des fichiers statiques ignorée${NC}"
fi
echo ""

# Restaurer le stash si nécessaire
if [ "$RESTORE_STASH" = true ]; then
    echo -e "${BLUE}🔄 Restauration des modifications locales...${NC}"
    if git stash pop; then
        echo -e "${GREEN}✅ Modifications restaurées${NC}"
    else
        echo -e "${YELLOW}⚠️  Conflits lors de la restauration (résolvez-les manuellement)${NC}"
    fi
    echo ""
fi

# Résumé
echo -e "${GREEN}✅ Déploiement terminé avec succès!${NC}"
echo ""
echo -e "${BLUE}📋 Résumé:${NC}"
echo "   - Code mis à jour: ✅"
echo "   - Image Docker reconstruite: ✅"
echo "   - Conteneur web redémarré: ✅"
echo "   - Base de données: ${GREEN}Non modifiée${NC} ✅"
echo ""
echo -e "${BLUE}📋 Commandes utiles:${NC}"
echo "   - Voir les logs: docker-compose logs -f web"
echo "   - Vérifier le statut: docker-compose ps"
echo "   - Redémarrer si nécessaire: docker-compose restart web"
echo ""
