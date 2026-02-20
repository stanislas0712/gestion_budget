# 🔐 Commandes SSL/Let's Encrypt - Résumé Rapide

## 📦 Installation Initiale

### 1. Installer Nginx et Certbot

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx

# CentOS/RHEL  
sudo yum install -y nginx certbot python3-certbot-nginx
```

### 2. Ouvrir les Ports Firewall

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 3. Configurer le Projet

```bash
# Créer les répertoires
mkdir -p certbot/conf certbot/www
chmod -R 755 certbot

# Rendre les scripts exécutables
chmod +x setup-ssl.sh renew-ssl.sh

# Mettre à jour .env avec :
# DOMAIN_NAME=budget.bkdb.bf
# LETSENCRYPT_EMAIL=votre-email@example.com
# DJANGO_USE_SSL=true
# DJANGO_ALLOWED_HOSTS=budget.bkdb.bf,www.budget.bkdb.bf
```

### 4. Installation Automatique du Certificat

```bash
./setup-ssl.sh
```

## 🔄 Renouvellement Automatique

### Configurer le Cron Job

```bash
crontab -e

# Ajouter cette ligne :
0 3 1 */3 * /chemin/vers/projet/renew-ssl.sh >> /var/log/certbot-renew.log 2>&1
```

### Renouvellement Manuel

```bash
./renew-ssl.sh
```

## ✅ Vérifications

```bash
# Tester SSL
curl -I https://budget.bkdb.bf

# Vérifier les certificats
docker run --rm -v "$(pwd)/certbot/conf:/etc/letsencrypt" certbot/certbot certificates

# Tester la config Nginx
docker-compose exec nginx nginx -t
```

## 🚀 Démarrage Production

```bash
docker-compose --profile production up -d
```
