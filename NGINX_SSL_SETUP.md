# Guide d'Installation Nginx avec SSL/Let's Encrypt pour budget.bkdb.bf

Ce guide explique comment installer et configurer Nginx avec SSL/Let's Encrypt pour le sous-domaine `budget.bkdb.bf`.

## 📋 Prérequis

1. Serveur avec accès root/sudo
2. Domaine `budget.bkdb.bf` pointant vers l'IP du serveur
3. Ports 80 et 443 ouverts dans le firewall
4. Docker et Docker Compose installés

## 🔧 Installation sur le Serveur

### 1. Installation de Nginx (si pas déjà installé)

```bash
# Sur Ubuntu/Debian
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# Sur CentOS/RHEL
sudo yum install -y nginx certbot python3-certbot-nginx

# Vérifier l'installation
nginx -v
certbot --version
```

### 2. Configuration du Firewall

```bash
# Autoriser HTTP et HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Vérifier le statut
sudo ufw status
```

### 3. Arrêter Nginx système (si installé)

Si Nginx est installé sur le système, arrêtez-le car nous utiliserons le conteneur Docker :

```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

## 🐳 Configuration Docker

### 1. Mettre à jour docker-compose.yml

Le service `nginx` doit être mis à jour pour inclure les volumes SSL :

```yaml
nginx:
  image: nginx:alpine
  container_name: budget_nginx
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx-ssl.conf:/etc/nginx/nginx-ssl.conf:ro
    - static_volume:/static:ro
    - media_volume:/media:ro
    - ./certbot/conf:/etc/letsencrypt:ro
    - ./certbot/www:/var/www/certbot:ro
  depends_on:
    - web
  networks:
    - budget_network
  restart: unless-stopped
  profiles:
    - production
```

### 2. Mettre à jour .env

Ajoutez dans votre fichier `.env` :

```env
# Domaine
DOMAIN_NAME=budget.bkdb.bf

# SSL Configuration
DJANGO_USE_SSL=true
DJANGO_ALLOWED_HOSTS=budget.bkdb.bf,www.budget.bkdb.bf

# Email pour Let's Encrypt
LETSENCRYPT_EMAIL=votre-email@example.com
```

### 3. Créer les répertoires pour Certbot

```bash
mkdir -p certbot/conf certbot/www
chmod -R 755 certbot
```

## 🔐 Installation du Certificat SSL

### Option 1 : Installation Automatique avec Certbot (Recommandé)

#### Étape 1 : Démarrer les services sans SSL

```bash
# Utiliser la configuration temporaire sans SSL
cp nginx-ssl.conf nginx.conf

# Démarrer les services
docker-compose --profile production up -d
```

#### Étape 2 : Obtenir le certificat Let's Encrypt

```bash
# Installer Certbot dans un conteneur temporaire
docker run -it --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email votre-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d budget.bkdb.bf \
  -d www.budget.bkdb.bf
```

#### Étape 3 : Activer la configuration SSL

```bash
# Restaurer la configuration SSL complète
# (nginx.conf contient déjà la config SSL)

# Redémarrer Nginx
docker-compose restart nginx
```

### Option 2 : Installation Manuelle avec Certbot sur le Serveur

```bash
# Obtenir le certificat
sudo certbot certonly --standalone \
  --email votre-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d budget.bkdb.bf \
  -d www.budget.bkdb.bf

# Copier les certificats vers le répertoire du projet
sudo cp -r /etc/letsencrypt/live/budget.bkdb.bf certbot/conf/live/
sudo cp -r /etc/letsencrypt/archive/budget.bkdb.bf certbot/conf/archive/
sudo chown -R $USER:$USER certbot
```

## 🔄 Renouvellement Automatique du Certificat

### Créer un script de renouvellement

Créez le fichier `renew-ssl.sh` :

```bash
#!/bin/bash
# Script de renouvellement automatique des certificats SSL

docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  certbot/certbot renew

# Redémarrer Nginx pour charger les nouveaux certificats
docker-compose restart nginx
```

Rendre le script exécutable :

```bash
chmod +x renew-ssl.sh
```

### Configurer un Cron Job

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne pour renouveler tous les 3 mois à 3h du matin
0 3 1 */3 * /chemin/vers/votre/projet/renew-ssl.sh >> /var/log/certbot-renew.log 2>&1
```

## ✅ Vérification

### 1. Vérifier que le certificat est valide

```bash
# Tester la connexion SSL
openssl s_client -connect budget.bkdb.bf:443 -servername budget.bkdb.bf

# Ou utiliser un outil en ligne
# https://www.ssllabs.com/ssltest/analyze.html?d=budget.bkdb.bf
```

### 2. Vérifier la configuration Nginx

```bash
# Tester la configuration
docker-compose exec nginx nginx -t

# Vérifier les logs
docker-compose logs nginx
```

### 3. Tester l'accès HTTPS

```bash
# Depuis votre navigateur
https://budget.bkdb.bf

# Ou avec curl
curl -I https://budget.bkdb.bf
```

## 🔧 Commandes Utiles

### Redémarrer Nginx

```bash
docker-compose restart nginx
```

### Voir les logs Nginx

```bash
docker-compose logs -f nginx
```

### Vérifier le statut des certificats

```bash
docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  certbot/certbot certificates
```

### Forcer le renouvellement (test)

```bash
docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  certbot/certbot renew --force-renewal

docker-compose restart nginx
```

## 🚨 Dépannage

### Le certificat n'est pas renouvelé automatiquement

1. Vérifier les permissions des répertoires :
```bash
ls -la certbot/
```

2. Vérifier les logs Certbot :
```bash
docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  certbot/certbot certificates
```

### Erreur 502 Bad Gateway

1. Vérifier que le service `web` est démarré :
```bash
docker-compose ps web
```

2. Vérifier la connectivité :
```bash
docker-compose exec nginx ping web
```

### Le domaine ne redirige pas vers HTTPS

1. Vérifier que `DJANGO_USE_SSL=true` dans `.env`
2. Vérifier que `ALLOWED_HOSTS` contient le domaine
3. Redémarrer tous les services :
```bash
docker-compose --profile production restart
```

## 📝 Notes Importantes

1. **Renouvellement** : Let's Encrypt expire tous les 90 jours. Configurez le renouvellement automatique.

2. **Backup** : Sauvegardez régulièrement le répertoire `certbot/conf`.

3. **Sécurité** : Ne commitez jamais les certificats dans Git. Ajoutez `certbot/` à `.gitignore`.

4. **Performance** : La configuration SSL inclut HTTP/2, OCSP Stapling et des headers de sécurité modernes.

## 🔗 Ressources

- [Documentation Let's Encrypt](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
