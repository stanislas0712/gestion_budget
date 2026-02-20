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
- ✅ Nginx (installé localement sur Ubuntu)
- ✅ Certbot (installé localement sur Ubuntu)
- ✅ Configuration du firewall
- ✅ Configuration SSL (optionnel)
- ✅ Renouvellement automatique (optionnel)

**Note importante:** Nginx et Certbot sont installés **localement sur le serveur Ubuntu**, pas dans Docker. Seul Django (web) tourne dans Docker.

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
# Configurer Nginx manuellement
chmod +x configure-nginx.sh
./configure-nginx.sh

# Démarrer l'application Django (Docker)
docker-compose --profile production up -d

# Vérifier SSL
curl -I https://budget.bkdb.bf

# Renouveler SSL manuellement
./renew-ssl.sh

# Voir les logs Nginx
sudo tail -f /var/log/nginx/budget-error.log
sudo tail -f /var/log/nginx/budget-access.log

# Tester la configuration Nginx
sudo nginx -t

# Redémarrer Nginx
sudo systemctl reload nginx
# ou
sudo systemctl restart nginx

# Voir la configuration Nginx
sudo cat /etc/nginx/sites-available/budget.bkdb.bf

# Pull Git en sécurité (gère les conflits)
chmod +x git-pull-safe.sh
./git-pull-safe.sh
```

## 🔧 Dépannage

### Erreur Django CSRF "La vérification CSRF a échoué"

Si vous obtenez l'erreur `La vérification CSRF a échoué` en production :

```bash
# Solution rapide
chmod +x fix-csrf-error.sh
./fix-csrf-error.sh
```

**Causes possibles:**
1. `CSRF_TRUSTED_ORIGINS` n'est pas configuré (requis depuis Django 4.0+)
2. `DJANGO_USE_SSL` n'est pas à `true` en production
3. Nginx ne transmet pas correctement `X-Forwarded-Proto`
4. Les cookies CSRF ne sont pas sécurisés

**Solutions manuelles:**

```bash
# 1. Mettre à jour .env
# Assurez-vous que .env contient:
DJANGO_USE_SSL=true
DOMAIN_NAME=budget.bkdb.bf

# 2. Vérifier la configuration Nginx
sudo grep "X-Forwarded-Proto" /etc/nginx/sites-available/budget.bkdb.bf
# Doit afficher: proxy_set_header X-Forwarded-Proto $scheme;

# 3. Redémarrer Django
docker-compose restart web
```

**Note:** `CSRF_TRUSTED_ORIGINS` est maintenant configuré automatiquement dans `config/settings/prod.py` en fonction de `DOMAIN_NAME`.

### Erreur Django "Invalid HTTP_HOST header"

Si vous obtenez l'erreur `Invalid HTTP_HOST header: 'localhost:8000'` :

```bash
# Solution rapide
chmod +x fix-django-allowed-hosts.sh
./fix-django-allowed-hosts.sh
```

**Causes possibles:**
1. `ALLOWED_HOSTS` ne contient pas le domaine ou l'IP du serveur
2. Nginx envoie le mauvais header `Host` à Django
3. Configuration `.env` incorrecte

**Solutions manuelles:**

```bash
# 1. Mettre à jour .env
# Ajoutez dans .env:
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,budget.bkdb.bf,www.budget.bkdb.bf,51.20.216.98

# 2. Vérifier la configuration Nginx
sudo grep "proxy_set_header Host" /etc/nginx/sites-available/budget.bkdb.bf
# Doit afficher: proxy_set_header Host $host;

# 3. Redémarrer Django
docker-compose restart web
```

### Erreur Let's Encrypt "Connection refused"

Si vous obtenez l'erreur `Connection refused` lors de l'obtention du certificat SSL :

```bash
# Solution rapide - Script de diagnostic
chmod +x fix-ssl-challenge.sh
./fix-ssl-challenge.sh
```

**Causes possibles:**
1. Nginx n'est pas démarré
2. Le port 80 n'est pas ouvert dans le firewall
3. Le domaine ne pointe pas vers le serveur
4. Nginx n'est pas configuré pour servir les challenges ACME

**Vérifications manuelles:**
```bash
# 1. Vérifier que Nginx est démarré (localement)
sudo systemctl status nginx

# 2. Vérifier que le port 80 est ouvert
sudo ufw status | grep 80
# ou
sudo firewall-cmd --list-ports

# 3. Vérifier le DNS
dig budget.bkdb.bf +short
# Doit retourner l'IP de votre serveur

# 4. Tester l'accès HTTP
curl -I http://budget.bkdb.bf

# 5. Tester le challenge manuellement
echo "test" | sudo tee /var/www/certbot/.well-known/acme-challenge/test.txt
curl http://budget.bkdb.bf/.well-known/acme-challenge/test.txt
```

### Erreur Docker "ContainerConfig"

Si vous obtenez l'erreur `KeyError: 'ContainerConfig'` :

```bash
# Solution rapide (recommandée)
chmod +x quick-fix-containerconfig.sh
./quick-fix-containerconfig.sh

# Ou solution interactive
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
