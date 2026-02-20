# 🚀 Installation Rapide Nginx + SSL pour budget.bkdb.bf

## 📋 Commandes d'Installation

### 1. Installation de Nginx et Certbot sur le Serveur

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# CentOS/RHEL
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

# Ou avec firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 3. Arrêter Nginx Système (si installé)

```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

### 4. Configuration du Projet

#### a. Mettre à jour le fichier `.env`

Ajoutez ces lignes dans votre fichier `.env` :

```env
# Domaine et SSL
DOMAIN_NAME=budget.bkdb.bf
LETSENCRYPT_EMAIL=votre-email@example.com
DJANGO_USE_SSL=true
DJANGO_ALLOWED_HOSTS=budget.bkdb.bf,www.budget.bkdb.bf

# Ports Nginx
NGINX_PORT=80
NGINX_SSL_PORT=443
```

#### b. Créer les répertoires pour les certificats

```bash
mkdir -p certbot/conf certbot/www
chmod -R 755 certbot
```

#### c. Rendre les scripts exécutables

```bash
chmod +x setup-ssl.sh
chmod +x renew-ssl.sh
```

### 5. Installation du Certificat SSL

#### Option A : Installation Automatique (Recommandé)

```bash
# Utiliser le script d'installation automatique
./setup-ssl.sh
```

#### Option B : Installation Manuelle

```bash
# Étape 1: Utiliser la configuration temporaire
cp nginx-ssl.conf nginx.conf

# Étape 2: Démarrer les services
docker-compose --profile production up -d

# Étape 3: Obtenir le certificat
docker run --rm \
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

# Étape 4: Restaurer la configuration SSL (nginx.conf contient déjà la config SSL)
# La configuration SSL est déjà dans nginx.conf

# Étape 5: Redémarrer Nginx
docker-compose --profile production restart nginx
```

### 6. Configuration du Renouvellement Automatique

#### Créer un Cron Job

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne pour renouveler tous les 3 mois à 3h du matin
0 3 1 */3 * /chemin/vers/votre/projet/renew-ssl.sh >> /var/log/certbot-renew.log 2>&1
```

#### Ou utiliser systemd timer (Alternative)

Créez `/etc/systemd/system/certbot-renew.service` :

```ini
[Unit]
Description=Renew Let's Encrypt certificates
After=docker.service

[Service]
Type=oneshot
WorkingDirectory=/chemin/vers/votre/projet
ExecStart=/chemin/vers/votre/projet/renew-ssl.sh
```

Créez `/etc/systemd/system/certbot-renew.timer` :

```ini
[Unit]
Description=Renew Let's Encrypt certificates monthly

[Timer]
OnCalendar=monthly
Persistent=true

[Install]
WantedBy=timers.target
```

Activez le timer :

```bash
sudo systemctl enable certbot-renew.timer
sudo systemctl start certbot-renew.timer
```

## ✅ Vérification

### 1. Vérifier que le certificat est valide

```bash
# Tester la connexion SSL
openssl s_client -connect budget.bkdb.bf:443 -servername budget.bkdb.bf

# Vérifier la date d'expiration
docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  certbot/certbot certificates
```

### 2. Tester l'accès HTTPS

```bash
# Depuis votre navigateur
https://budget.bkdb.bf

# Ou avec curl
curl -I https://budget.bkdb.bf
```

### 3. Vérifier la configuration Nginx

```bash
# Tester la configuration
docker-compose exec nginx nginx -t

# Voir les logs
docker-compose logs nginx
```

## 🔧 Commandes Utiles

### Redémarrer Nginx

```bash
docker-compose --profile production restart nginx
```

### Voir les logs en temps réel

```bash
docker-compose --profile production logs -f nginx
```

### Forcer le renouvellement (test)

```bash
docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  certbot/certbot renew --force-renewal

docker-compose --profile production restart nginx
```

### Vérifier le statut des certificats

```bash
docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  certbot/certbot certificates
```

## 🚨 Dépannage

### Le certificat n'est pas créé

1. Vérifier que le domaine pointe vers le serveur :
```bash
dig budget.bkdb.bf
# ou
nslookup budget.bkdb.bf
```

2. Vérifier que les ports 80 et 443 sont ouverts :
```bash
sudo netstat -tulpn | grep -E ':(80|443)'
```

3. Vérifier les logs Certbot :
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

1. **Sécurité** : Ne commitez jamais les certificats dans Git (déjà dans `.gitignore`)
2. **Backup** : Sauvegardez régulièrement le répertoire `certbot/conf`
3. **Renouvellement** : Les certificats Let's Encrypt expirent tous les 90 jours
4. **Performance** : La configuration inclut HTTP/2, OCSP Stapling et des headers de sécurité

## 🔗 Ressources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
