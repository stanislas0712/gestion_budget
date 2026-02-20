# 📝 Configuration Nginx pour budget.bkdb.bf

Ce guide explique comment configurer Nginx manuellement pour le domaine `budget.bkdb.bf`.

## 🚀 Configuration Automatique (Recommandé)

```bash
# Utiliser le script automatique
chmod +x configure-nginx.sh
./configure-nginx.sh
```

Le script vous proposera 3 options :
1. **HTTP uniquement** - Pour obtenir le certificat SSL
2. **HTTP + HTTPS** - Configuration complète avec SSL
3. **HTTPS uniquement** - Redirection HTTP vers HTTPS

## 📋 Configuration Manuelle

### 1. Créer le fichier de configuration

```bash
sudo nano /etc/nginx/sites-available/budget.bkdb.bf
```

### 2. Configuration HTTP uniquement (pour obtenir le certificat)

```nginx
server {
    listen 80;
    server_name budget.bkdb.bf www.budget.bkdb.bf;
    client_max_body_size 100M;

    # Logs
    access_log /var/log/nginx/budget-access.log;
    error_log /var/log/nginx/budget-error.log;

    # Acme Challenge pour Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Proxy vers Django (Docker)
    location / {
        proxy_pass http://localhost:8000;
        # IMPORTANT: Envoyer le domaine dans le header Host, pas localhost:8000
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 3. Configuration HTTP + HTTPS (avec certificat SSL)

```nginx
# Redirection HTTP vers HTTPS
server {
    listen 80;
    server_name budget.bkdb.bf www.budget.bkdb.bf;
    client_max_body_size 100M;

    # Logs
    access_log /var/log/nginx/budget-access.log;
    error_log /var/log/nginx/budget-error.log;

    # Acme Challenge pour Let's Encrypt (renouvellement)
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirection vers HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Configuration HTTPS
server {
    listen 443 ssl http2;
    server_name budget.bkdb.bf www.budget.bkdb.bf;
    client_max_body_size 100M;

    # Logs
    access_log /var/log/nginx/budget-ssl-access.log;
    error_log /var/log/nginx/budget-ssl-error.log;

    # Certificats SSL Let's Encrypt
    ssl_certificate /etc/letsencrypt/live/budget.bkdb.bf/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/budget.bkdb.bf/privkey.pem;

    # Configuration SSL moderne et sécurisée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Headers de sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy vers Django (Docker)
    location / {
        proxy_pass http://localhost:8000;
        # IMPORTANT: Envoyer le domaine dans le header Host, pas localhost:8000
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 4. Activer la configuration

```bash
# Créer le lien symbolique
sudo ln -s /etc/nginx/sites-available/budget.bkdb.bf /etc/nginx/sites-enabled/

# Tester la configuration
sudo nginx -t

# Redémarrer Nginx
sudo systemctl reload nginx
```

## 🔧 Commandes Utiles

```bash
# Voir la configuration
sudo cat /etc/nginx/sites-available/budget.bkdb.bf

# Éditer la configuration
sudo nano /etc/nginx/sites-available/budget.bkdb.bf

# Tester la configuration
sudo nginx -t

# Recharger Nginx (sans interruption)
sudo systemctl reload nginx

# Redémarrer Nginx
sudo systemctl restart nginx

# Voir le statut de Nginx
sudo systemctl status nginx

# Voir les logs
sudo tail -f /var/log/nginx/budget-error.log
sudo tail -f /var/log/nginx/budget-access.log

# Désactiver le site
sudo rm /etc/nginx/sites-enabled/budget.bkdb.bf
sudo systemctl reload nginx
```

## 📁 Emplacements des Fichiers

- **Configuration**: `/etc/nginx/sites-available/budget.bkdb.bf`
- **Lien activé**: `/etc/nginx/sites-enabled/budget.bkdb.bf`
- **Logs d'accès**: `/var/log/nginx/budget-access.log`
- **Logs d'erreur**: `/var/log/nginx/budget-error.log`
- **Certificats SSL**: `/etc/letsencrypt/live/budget.bkdb.bf/`
- **Challenges ACME**: `/var/www/certbot/.well-known/acme-challenge/`

## 🔍 Dépannage

### Erreur "nginx: [emerg] bind() to 0.0.0.0:80 failed"

Le port 80 est déjà utilisé. Vérifiez :

```bash
# Voir ce qui utilise le port 80
sudo netstat -tlnp | grep :80
sudo lsof -i :80

# Arrêter le service qui utilise le port 80
sudo systemctl stop apache2  # Si Apache est installé
```

### Erreur "502 Bad Gateway"

Le service Django n'est pas accessible :

```bash
# Vérifier que Django est démarré
docker-compose ps web

# Vérifier que le port 8000 est accessible
curl http://localhost:8000
```

### Erreur de certificat SSL

```bash
# Vérifier que le certificat existe
sudo ls -la /etc/letsencrypt/live/budget.bkdb.bf/

# Vérifier les permissions
sudo chown -R www-data:www-data /etc/letsencrypt/live/
```
