from .base import *  # noqa

DEBUG = True

if not SECRET_KEY:
    # Development convenience only
    SECRET_KEY = "dev-insecure-change-me"

ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1"]

# Utiliser SQLite pour le développement (plus simple, pas besoin de serveur)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3')
    }
}