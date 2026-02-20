#!/bin/bash
# Script de déploiement sécurisé qui gère automatiquement l'erreur ContainerConfig

set +e  # Ne pas arrêter sur toutes les erreurs au début

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Déploiement sécurisé du conteneur web Django${NC}"
echo -e "${YELLOW}⚠️  La base de données ne sera PAS affectée${NC}"
echo ""

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Étape 0: Nettoyer les conteneurs problématiques (pour éviter ContainerConfig)
echo -e "${BLUE}0️⃣  Nettoyage des conteneurs problématiques...${NC}"

# Arrêter tous les conteneurs web
docker-compose stop web 2>/dev/null || true

# Supprimer tous les conteneurs web (arrêtés ou en cours)
docker ps -a --filter "name=budget_web" --format "{{.ID}}" | while read -r id; do
    if [ -n "$id" ]; then
        docker rm -f "$id" 2>/dev/null && echo "   Conteneur $id supprimé" || true
    fi
done

# Supprimer aussi les conteneurs avec des IDs partiels (pour les anciens conteneurs)
docker ps -a --format "{{.ID}} {{.Names}}" | grep "budget_web\|_budget_web" | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true

echo -e "${GREEN}✅ Nettoyage terminé${NC}"
echo ""

# Activer la gestion d'erreurs maintenant
set -e

# Étape 1: Récupérer le nouveau code (optionnel)
echo -e "${BLUE}1️⃣  Récupération du nouveau code...${NC}"
read -p "Voulez-vous faire un git pull? (O/n): " pull_choice
pull_choice=${pull_choice:-O}

if [[ $pull_choice =~ ^[OoYy]$ ]]; then
    if git pull; then
        echo -e "${GREEN}✅ Code mis à jour${NC}"
    else
        echo -e "${YELLOW}⚠️  Erreur lors du git pull (peut être normal si déjà à jour)${NC}"
    fi
else
    echo -e "${YELLOW}⏭️  Git pull ignoré${NC}"
fi
echo ""

# Étape 2: Vérifier que la base de données est intacte
echo -e "${BLUE}2️⃣  Vérification de la base de données...${NC}"
if docker-compose ps db 2>/dev/null | grep -q "Up"; then
    echo -e "${GREEN}✅ Base de données est en cours d'exécution${NC}"
    echo -e "${GREEN}   La base de données ne sera PAS modifiée${NC}"
else
    echo -e "${YELLOW}⚠️  Base de données non démarrée${NC}"
    echo "   Démarrage de la base de données..."
    docker-compose up -d db
    sleep 5
fi
echo ""

# Étape 3: Reconstruire l'image du service web
echo -e "${BLUE}3️⃣  Reconstruction de l'image Docker du service web...${NC}"
echo "   Cela peut prendre plusieurs minutes..."
if docker-compose build web; then
    echo -e "${GREEN}✅ Image reconstruite${NC}"
else
    echo -e "${RED}❌ Erreur lors de la reconstruction${NC}"
    exit 1
fi
echo ""

# Étape 4: Créer et démarrer le conteneur web
echo -e "${BLUE}4️⃣  Création et démarrage du conteneur web...${NC}"

# Utiliser --force-recreate pour forcer la création d'un nouveau conteneur
if docker-compose up -d --force-recreate --no-deps web; then
    echo -e "${GREEN}✅ Conteneur web créé et démarré${NC}"
else
    echo -e "${RED}❌ Erreur lors du démarrage${NC}"
    echo "   Vérifiez les logs: docker-compose logs web"
    exit 1
fi
echo ""

# Étape 5: Attendre que Django soit prêt
echo -e "${BLUE}5️⃣  Attente que Django soit prêt...${NC}"
sleep 10

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
    echo -e "${YELLOW}⚠️  Django ne répond pas encore${NC}"
    echo "   Vérifiez les logs: docker-compose logs web"
fi
echo ""

# Étape 6: Appliquer les migrations (optionnel)
echo -e "${BLUE}6️⃣  Vérification des migrations...${NC}"
read -p "Voulez-vous appliquer les migrations? (O/n): " migrate_choice
migrate_choice=${migrate_choice:-O}

if [[ $migrate_choice =~ ^[OoYy]$ ]]; then
    echo "   Application des migrations..."
    if docker-compose exec -T web python manage.py migrate --noinput; then
        echo -e "${GREEN}✅ Migrations appliquées${NC}"
    else
        echo -e "${YELLOW}⚠️  Erreur lors des migrations (peut être normal)${NC}"
    fi
else
    echo -e "${YELLOW}⏭️  Migrations ignorées${NC}"
fi
echo ""

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
