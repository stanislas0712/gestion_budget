"""Configuration package (settings/urls/asgi/wsgi)."""

# Import Celery pour qu'il soit chargé au démarrage de Django
from .celery import app as celery_app

__all__ = ('celery_app',)