from .base import *  # noqa

DEBUG = os.environ.get("DJANGO_DEBUG", "0") in {"1", "true", "True", "yes"}

if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY doit être défini en production.")

# S'assurer que ALLOWED_HOSTS contient au moins localhost et 0.0.0.0 pour Docker
# Ajouter le domaine depuis les variables d'environnement si défini
DOMAIN_NAME = os.environ.get("DOMAIN_NAME", "")
if DOMAIN_NAME:
    if not ALLOWED_HOSTS:
        ALLOWED_HOSTS = []
    if DOMAIN_NAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(DOMAIN_NAME)
    if f"www.{DOMAIN_NAME}" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(f"www.{DOMAIN_NAME}")

# Toujours ajouter localhost, 127.0.0.1, 0.0.0.0 pour les accès locaux et Docker
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = []
    
# Ajouter les hôtes par défaut s'ils ne sont pas déjà présents
default_hosts = ["localhost", "127.0.0.1", "0.0.0.0"]
for host in default_hosts:
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

# Ajouter l'IP du serveur depuis les variables d'environnement si disponible
# Cela évite l'erreur "Invalid HTTP_HOST header: '51.20.216.98:8000'"
# Note: Django extrait automatiquement l'IP du header Host (sans le port)
SERVER_IP = os.environ.get("SERVER_IP", "")
if SERVER_IP and SERVER_IP not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(SERVER_IP)

# Désactiver les redirections HTTPS si pas de proxy SSL (pour Docker en développement)
# En production avec Nginx/SSL, Nginx gère la redirection HTTP → HTTPS
# Donc on désactive SECURE_SSL_REDIRECT pour éviter les boucles de redirection
USE_SSL = os.environ.get("DJANGO_USE_SSL", "false").lower() in {"true", "1", "yes"}

CSRF_COOKIE_SECURE = USE_SSL
SESSION_COOKIE_SECURE = USE_SSL
# IMPORTANT: Désactiver SECURE_SSL_REDIRECT car Nginx gère déjà la redirection
# Sinon il y aura une double redirection (Nginx → HTTPS, puis Django → HTTPS)
SECURE_SSL_REDIRECT = False  # Nginx gère la redirection HTTP → HTTPS
if USE_SSL:
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

DATABASES = {
    'default': {
        # Utiliser PostgreSQL standard au lieu de PostGIS (pas de fonctionnalités géospatiales nécessaires)
        # Si PostGIS est nécessaire plus tard, installer l'extension dans le conteneur PostgreSQL
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("DB_NAME"),
        'USER': os.environ.get("DB_USER"),
        'PASSWORD': os.environ.get("DB_PASSWORD"),
        'HOST': os.environ.get("DB_HOST"),
        'PORT': os.environ.get("DB_PORT"),
        'CONN_MAX_AGE': int(os.environ.get("DB_CONN_MAX_AGE", "60")),
    }
}