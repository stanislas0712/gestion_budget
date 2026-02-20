# 🔐 Installation Complète - budget.bkdb.bf

## 🚀 Installation Automatique (Recommandé)

```bash
# Rendre tous les scripts exécutables (recommandé)
chmod +x *.sh

# Ou rendre uniquement install.sh
chmod +x install.sh

# Lancer l'installation complète
./install.sh
```

Le script `install.sh` installe automatiquement :
- ✅ Git
- ✅ Docker et Docker Compose
- ✅ Nginx
- ✅ Certbot
- ✅ Configuration du firewall
- ✅ Configuration SSL (optionnel)
- ✅ Renouvellement automatique (optionnel)

## 📋 Installation Manuelle

### 1. Installation Rapide

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y git docker.io docker-compose nginx certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install -y git docker docker-compose nginx certbot python3-certbot-nginx
```

### 2. Configuration

```bash
# Créer les répertoires
mkdir -p certbot/conf certbot/www

# Configurer les permissions (si nécessaire)
# Si erreur "Operation not permitted", essayer:
sudo chown -R $USER:$USER certbot
chmod -R 755 certbot

# Ou si les répertoires existent déjà avec root:
sudo chown -R $USER:$USER certbot && chmod -R 755 certbot

# Configurer .env
# DOMAIN_NAME=budget.bkdb.bf
# LETSENCRYPT_EMAIL=votre-email@example.com
# DJANGO_USE_SSL=true
# DJANGO_ALLOWED_HOSTS=budget.bkdb.bf,www.budget.bkdb.bf
```

### 3. Installation SSL

```bash
# Rendre le script exécutable (si nécessaire)
chmod +x setup-ssl.sh

# Lancer l'installation SSL
./setup-ssl.sh
```

### 4. Renouvellement Automatique

```bash
crontab -e
# Ajouter: 0 3 1 */3 * /chemin/vers/projet/renew-ssl.sh >> /var/log/certbot-renew.log 2>&1
```

## ✅ Commandes Utiles

```bash
# Démarrer l'application
docker-compose --profile production up -d

# Vérifier SSL
curl -I https://budget.bkdb.bf

# Renouveler SSL manuellement
./renew-ssl.sh

# Voir les logs
docker-compose logs -f nginx

# Pull Git en sécurité (gère les conflits)
chmod +x git-pull-safe.sh
./git-pull-safe.sh
```

## 🔧 Dépannage

### Erreur Docker "ContainerConfig"

Si vous obtenez l'erreur `KeyError: 'ContainerConfig'` :

```bash
# Solution rapide
chmod +x fix-docker-error.sh
./fix-docker-error.sh
```

**Solutions manuelles:**

```bash
# 1. Arrêter et supprimer tous les conteneurs
docker-compose --profile production down
docker container prune -f

# 2. Supprimer les conteneurs problématiques
docker ps -a --filter "name=budget_" --format "{{.ID}}" | xargs -r docker rm -f

# 3. Reconstruire les images
docker-compose --profile production build --no-cache

# 4. Redémarrer
docker-compose --profile production up -d
```

### Erreur "Permission denied" avec les scripts

Si vous obtenez `Permission denied` lors de l'exécution d'un script :

```bash
# Rendre le script exécutable
chmod +x setup-ssl.sh
chmod +x renew-ssl.sh
chmod +x fix-certbot-permissions.sh
chmod +x install.sh

# Ou tous en une fois
chmod +x *.sh
```

### Erreur "Operation not permitted" avec chmod

Si vous obtenez cette erreur lors de la création des répertoires certbot :

**Solution rapide (recommandée):**
```bash
chmod +x fix-certbot-permissions.sh
./fix-certbot-permissions.sh
```

**Solutions manuelles:**

```bash
# Solution 1: Changer le propriétaire puis les permissions
sudo chown -R $USER:$USER certbot
chmod -R 755 certbot

# Solution 2: Si les répertoires n'existent pas encore
mkdir -p certbot/conf certbot/www
sudo chown -R $USER:$USER certbot
chmod -R 755 certbot

# Solution 3: Supprimer et recréer (si les répertoires existent déjà)
sudo rm -rf certbot
mkdir -p certbot/conf certbot/www
chmod -R 755 certbot
```

**Note:** Les permissions ne sont pas critiques pour Docker. Si `chmod` échoue, Docker devrait quand même fonctionner avec les permissions par défaut.
