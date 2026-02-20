#!/bin/bash
# Script d'installation complète : Docker, Git, Nginx, Certbot pour budget.bkdb.bf
# Usage: ./install.sh

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Installation Complète: Docker, Git, Nginx, Certbot SSL    ║${NC}"
echo -e "${BLUE}║  pour budget.bkdb.bf                                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Détection du système d'exploitation
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
elif type lsb_release >/dev/null 2>&1; then
    OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
    VER=$(lsb_release -sr)
else
    echo -e "${RED}❌ Impossible de détecter le système d'exploitation${NC}"
    exit 1
fi

echo -e "${GREEN}📋 Système détecté: $OS $VER${NC}"
echo ""

# ============================================================================
# 1. INSTALLATION DE GIT
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 ÉTAPE 1: Installation de Git${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if command -v git &> /dev/null; then
    echo -e "${GREEN}✅ Git est déjà installé: $(git --version)${NC}"
else
    echo "📥 Installation de Git..."
    case $OS in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y git
            ;;
        centos|rhel|fedora)
            sudo yum install -y git
            ;;
        *)
            echo -e "${YELLOW}⚠️  Système non supporté. Installez Git manuellement.${NC}"
            ;;
    esac
    echo -e "${GREEN}✅ Git installé: $(git --version)${NC}"
fi
echo ""

# ============================================================================
# 2. INSTALLATION DE DOCKER
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🐳 ÉTAPE 2: Installation de Docker${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker est déjà installé: $(docker --version)${NC}"
else
    echo "📥 Installation de Docker..."
    case $OS in
        ubuntu|debian)
            # Supprimer les anciennes versions
            sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
            
            # Installer les prérequis
            sudo apt update
            sudo apt install -y ca-certificates curl gnupg lsb-release
            
            # Ajouter la clé GPG officielle de Docker
            sudo mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            
            # Ajouter le dépôt Docker
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Installer Docker
            sudo apt update
            sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
        centos|rhel)
            # Installer les prérequis
            sudo yum install -y yum-utils
            
            # Ajouter le dépôt Docker
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            
            # Installer Docker
            sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
        *)
            echo -e "${YELLOW}⚠️  Système non supporté. Installez Docker manuellement.${NC}"
            ;;
    esac
    
    # Démarrer Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Ajouter l'utilisateur au groupe docker (pour éviter sudo)
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}✅ Docker installé: $(docker --version)${NC}"
    echo -e "${YELLOW}⚠️  Vous devez vous déconnecter/reconnecter pour utiliser Docker sans sudo${NC}"
fi

# Vérifier Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo -e "${GREEN}✅ Docker Compose est disponible${NC}"
else
    echo -e "${RED}❌ Docker Compose n'est pas installé${NC}"
    exit 1
fi
echo ""

# ============================================================================
# 3. INSTALLATION DE NGINX ET CERTBOT
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🌐 ÉTAPE 3: Installation de Nginx et Certbot${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if command -v nginx &> /dev/null; then
    echo -e "${GREEN}✅ Nginx est déjà installé: $(nginx -v 2>&1)${NC}"
    # Arrêter Nginx système si installé (on utilise Docker)
    if systemctl is-active --quiet nginx; then
        echo "🛑 Arrêt de Nginx système (on utilise Docker)..."
        sudo systemctl stop nginx
        sudo systemctl disable nginx
    fi
else
    echo "📥 Installation de Nginx..."
    case $OS in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y nginx
            sudo systemctl stop nginx
            sudo systemctl disable nginx
            ;;
        centos|rhel)
            sudo yum install -y nginx
            sudo systemctl stop nginx
            sudo systemctl disable nginx
            ;;
    esac
    echo -e "${GREEN}✅ Nginx installé${NC}"
fi

if command -v certbot &> /dev/null; then
    echo -e "${GREEN}✅ Certbot est déjà installé: $(certbot --version)${NC}"
else
    echo "📥 Installation de Certbot..."
    case $OS in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y certbot python3-certbot-nginx
            ;;
        centos|rhel)
            sudo yum install -y certbot python3-certbot-nginx
            ;;
    esac
    echo -e "${GREEN}✅ Certbot installé: $(certbot --version)${NC}"
fi
echo ""

# ============================================================================
# 4. CONFIGURATION DU FIREWALL
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔥 ÉTAPE 4: Configuration du Firewall${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Détecter le type de firewall
if command -v ufw &> /dev/null; then
    echo "📥 Configuration de UFW..."
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    echo -e "${GREEN}✅ Ports 80 et 443 ouverts avec UFW${NC}"
elif command -v firewall-cmd &> /dev/null; then
    echo "📥 Configuration de firewalld..."
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --reload
    echo -e "${GREEN}✅ Ports 80 et 443 ouverts avec firewalld${NC}"
else
    echo -e "${YELLOW}⚠️  Aucun firewall détecté. Assurez-vous que les ports 80 et 443 sont ouverts.${NC}"
fi
echo ""

# ============================================================================
# 5. CONFIGURATION DU PROJET
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📁 ÉTAPE 5: Configuration du Projet${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Créer les répertoires pour Certbot
echo "📁 Création des répertoires..."
mkdir -p certbot/conf certbot/www

# Essayer de changer les permissions (peut échouer si les répertoires appartiennent à root)
if chmod -R 755 certbot 2>/dev/null; then
    echo -e "${GREEN}✅ Permissions configurées${NC}"
elif sudo chmod -R 755 certbot 2>/dev/null; then
    echo -e "${GREEN}✅ Permissions configurées (avec sudo)${NC}"
    # Changer le propriétaire pour éviter les problèmes futurs
    sudo chown -R $USER:$USER certbot 2>/dev/null || true
else
    echo -e "${YELLOW}⚠️  Impossible de changer les permissions (non critique)${NC}"
    # Essayer de changer le propriétaire si les répertoires existent déjà
    if [ -d "certbot" ]; then
        sudo chown -R $USER:$USER certbot 2>/dev/null || true
    fi
fi
echo -e "${GREEN}✅ Répertoires créés${NC}"

# Rendre les scripts exécutables
echo "🔧 Rendre les scripts exécutables..."
SCRIPTS=("setup-ssl.sh" "renew-ssl.sh" "fix-certbot-permissions.sh" "make-executable.sh" "git-pull-safe.sh")
for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if chmod +x "$script" 2>/dev/null; then
            echo -e "${GREEN}✅ $script rendu exécutable${NC}"
        elif sudo chmod +x "$script" 2>/dev/null; then
            echo -e "${GREEN}✅ $script rendu exécutable (avec sudo)${NC}"
        else
            echo -e "${YELLOW}⚠️  Impossible de rendre $script exécutable${NC}"
        fi
    fi
done

# Vérifier le fichier .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Fichier .env non trouvé. Création depuis env.example...${NC}"
    if [ -f "env.example" ]; then
        cp env.example .env
        echo -e "${GREEN}✅ Fichier .env créé.${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: Éditez .env et configurez:${NC}"
        echo "   - DOMAIN_NAME=budget.bkdb.bf"
        echo "   - LETSENCRYPT_EMAIL=votre-email@example.com"
        echo "   - DJANGO_USE_SSL=true"
        echo "   - DJANGO_ALLOWED_HOSTS=budget.bkdb.bf,www.budget.bkdb.bf"
    else
        echo -e "${RED}❌ env.example non trouvé${NC}"
    fi
else
    echo -e "${GREEN}✅ Fichier .env trouvé${NC}"
    echo -e "${YELLOW}⚠️  Vérifiez que .env contient:${NC}"
    echo "   - DOMAIN_NAME=budget.bkdb.bf"
    echo "   - LETSENCRYPT_EMAIL=votre-email@example.com"
    echo "   - DJANGO_USE_SSL=true"
    echo "   - DJANGO_ALLOWED_HOSTS=budget.bkdb.bf,www.budget.bkdb.bf"
fi
echo ""

# ============================================================================
# 6. INSTALLATION DU CERTIFICAT SSL (OPTIONNEL)
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔐 ÉTAPE 6: Installation du Certificat SSL (Optionnel)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

read -p "Voulez-vous installer le certificat SSL maintenant? (o/N): " install_ssl

if [[ $install_ssl =~ ^[OoYy]$ ]]; then
    # Charger les variables d'environnement
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    DOMAIN="${DOMAIN_NAME:-budget.bkdb.bf}"
    EMAIL="${LETSENCRYPT_EMAIL:-}"
    
    if [ -z "$EMAIL" ]; then
        echo -e "${RED}❌ LETSENCRYPT_EMAIL n'est pas défini dans .env${NC}"
        echo "   Ajoutez: LETSENCRYPT_EMAIL=votre-email@example.com"
    else
        echo "🔐 Installation du certificat SSL pour $DOMAIN..."
        
        # Utiliser la configuration temporaire
        if [ -f nginx.conf ]; then
            cp nginx.conf nginx.conf.backup 2>/dev/null || true
        fi
        cp nginx-ssl.conf nginx.conf
        
        # Démarrer les services
        echo "🚀 Démarrage des services..."
        docker-compose --profile production up -d web
        sleep 5
        docker-compose --profile production up -d nginx
        sleep 5
        
        # Obtenir le certificat
        docker run --rm \
          -v "$SCRIPT_DIR/certbot/conf:/etc/letsencrypt" \
          -v "$SCRIPT_DIR/certbot/www:/var/www/certbot" \
          certbot/certbot certonly \
          --webroot \
          --webroot-path=/var/www/certbot \
          --email "$EMAIL" \
          --agree-tos \
          --no-eff-email \
          --non-interactive \
          -d "$DOMAIN" \
          -d "www.$DOMAIN"
        
        if [ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
            echo -e "${GREEN}✅ Certificat SSL installé avec succès${NC}"
            
            # Restaurer la configuration SSL
            if [ -f nginx.conf.backup ]; then
                # La config SSL est déjà dans nginx.conf (écrite par le script)
                echo "📝 Configuration SSL activée"
            fi
            
            # Redémarrer Nginx
            docker-compose --profile production restart nginx
            echo -e "${GREEN}✅ Nginx redémarré avec SSL${NC}"
        else
            echo -e "${RED}❌ Erreur lors de l'installation du certificat${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⏭️  Installation SSL ignorée. Vous pouvez l'installer plus tard avec:${NC}"
    echo "   ./setup-ssl.sh"
fi
echo ""

# ============================================================================
# 7. CONFIGURATION DU RENOUVELLEMENT AUTOMATIQUE
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔄 ÉTAPE 7: Configuration du Renouvellement Automatique${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

read -p "Voulez-vous configurer le renouvellement automatique SSL? (o/N): " setup_cron

if [[ $setup_cron =~ ^[OoYy]$ ]]; then
    CRON_CMD="0 3 1 */3 * $SCRIPT_DIR/renew-ssl.sh >> /var/log/certbot-renew.log 2>&1"
    
    # Vérifier si la ligne existe déjà
    if crontab -l 2>/dev/null | grep -q "renew-ssl.sh"; then
        echo -e "${YELLOW}⚠️  Le renouvellement automatique est déjà configuré${NC}"
    else
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo -e "${GREEN}✅ Renouvellement automatique configuré${NC}"
        echo "   La commande sera exécutée tous les 3 mois à 3h du matin"
    fi
else
    echo -e "${YELLOW}⏭️  Renouvellement automatique ignoré.${NC}"
    echo "   Pour le configurer plus tard, ajoutez au crontab:"
    echo "   0 3 1 */3 * $SCRIPT_DIR/renew-ssl.sh >> /var/log/certbot-renew.log 2>&1"
fi
echo ""

# ============================================================================
# RÉSUMÉ
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Installation terminée!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}📋 Récapitulatif:${NC}"
echo "   ✅ Git installé"
echo "   ✅ Docker installé"
echo "   ✅ Nginx installé"
echo "   ✅ Certbot installé"
echo "   ✅ Firewall configuré"
echo "   ✅ Répertoires créés"
echo ""
echo -e "${YELLOW}📝 Prochaines étapes:${NC}"
echo "   1. Vérifiez/éditez le fichier .env"
echo "   2. Assurez-vous que le domaine budget.bkdb.bf pointe vers ce serveur"
echo "   3. Si SSL n'est pas installé, exécutez: ./setup-ssl.sh"
echo "   4. Démarrez l'application: docker-compose --profile production up -d"
echo ""
echo -e "${GREEN}🌐 Votre application sera accessible sur:${NC}"
echo "   - http://budget.bkdb.bf (redirigera vers HTTPS)"
echo "   - https://budget.bkdb.bf"
echo ""
