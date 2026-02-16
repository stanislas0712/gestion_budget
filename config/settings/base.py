from __future__ import annotations

import os,sys
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Patch pour Django 4.2 avec Python 3.14 - fix du bug __dict__ dans context.py
import django.template.context

# Patch aussi bind_template pour garantir _processors_index
from contextlib import contextmanager

_original_bind_template = django.template.context.RequestContext.bind_template

@contextmanager
def _patched_bind_template(self, template):
    """Patch pour garantir que _processors_index existe avant bind_template"""
    if hasattr(self, 'request') and not hasattr(self, '_processors_index'):
        # Si _processors_index n'existe pas, le définir
        if len(self.dicts) >= 2:
            self._processors_index = len(self.dicts) - 2
        else:
            self._processors_index = len(self.dicts) if self.dicts else 0
    # Appeler la méthode originale
    with _original_bind_template(self, template):
        yield

django.template.context.RequestContext.bind_template = _patched_bind_template

def _patched_context_copy(self):
    """Patch pour corriger le bug 'super' object has no attribute 'dicts' avec Python 3.14"""
    # Sauvegarder tous les attributs importants AVANT de créer le duplicate
    original_processors_index = getattr(self, '_processors_index', None)
    original_processors = getattr(self, '_processors', None)
    original_request = getattr(self, 'request', None)
    
    # Pour RequestContext, il faut passer request en argument
    if original_request is not None:
        # Créer le duplicate avec le request et le premier dict
        duplicate = self.__class__(original_request, self.dicts[0] if self.dicts else {})
    else:
        duplicate = self.__class__(self.dicts[0] if self.dicts else {})
    
    # Copier dicts - cela va changer la longueur, donc _processors_index doit être ajusté
    duplicate.dicts = self.dicts[:]
    duplicate.autoescape = self.autoescape
    
    # Copier les autres attributs si nécessaire (pour RequestContext)
    if original_request is not None:
        duplicate.request = original_request
    if original_processors is not None:
        # _processors doit être un tuple, pas une liste
        duplicate._processors = tuple(original_processors) if original_processors else ()
    
    # _processors_index doit TOUJOURS être défini pour RequestContext
    # Il pointe vers l'index dans dicts où les processors sont stockés
    if original_request is not None:
        # Vérifier si c'est vraiment un RequestContext
        from django.template.context import RequestContext
        if isinstance(self, RequestContext) or isinstance(duplicate, RequestContext):
            # Toujours définir _processors_index pour RequestContext
            if original_processors_index is not None:
                # Si l'original avait _processors_index, l'utiliser directement
                duplicate._processors_index = original_processors_index
            else:
                # Sinon, le recalculer: dans RequestContext.__init__, c'est len(dicts) avant les deux update({})
                # Après __init__, il y a 2 dicts de plus, donc normalement c'est len(dicts) - 2
                # Mais si nous copions tous les dicts, _processors_index devrait être le même que l'original
                # Si l'original n'a pas _processors_index, utilisons len(dicts) - 2
                if len(duplicate.dicts) >= 2:
                    duplicate._processors_index = len(duplicate.dicts) - 2
                else:
                    duplicate._processors_index = len(duplicate.dicts) if duplicate.dicts else 0
        # S'assurer que _processors_index est toujours défini si request existe
        if not hasattr(duplicate, '_processors_index'):
            duplicate._processors_index = len(duplicate.dicts) - 2 if len(duplicate.dicts) >= 2 else len(duplicate.dicts) if duplicate.dicts else 0
    return duplicate

# Appliquer le patch aux deux classes de contexte
django.template.context.Context.__copy__ = _patched_context_copy
django.template.context.RequestContext.__copy__ = _patched_context_copy

# Load local .env if present (not committed). This is safe in prod too (no-op if missing).
load_dotenv()

# config/settings/base.py -> config/settings -> config -> project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENV_PATH = BASE_DIR / "security.env"

load_dotenv(dotenv_path=ENV_PATH)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") in {"1", "true", "True", "yes"}

allowed_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts.split(",") if h.strip()]

INSTALLED_APPS = [
    # Django core
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Third-party
    "rest_framework",
    "django_htmx",
    "auditlog",
    "simple_history",
    "django_filters",

    # Local apps
    "apps.integrations",
    "apps.operators",
    "apps.projects",
    "apps.conventions",
    "apps.budgets",
    "apps.workflow",
    "apps.exports",
    "apps.audits",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny', # À changer en IsAuthenticated plus tard
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ]
}
ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.budgets.context_processors.appel_a_projet_context",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


AUTH_PASSWORD_VALIDATORS = [
    # Validation minimale - Permet des mots de passe simples (chiffres uniquement)
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 4}},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Simple History
SIMPLE_HISTORY_HISTORY_CHANGE_REASON_USE_TEXT_FIELD = True

# Authentication
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/budgets/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Security defaults (harden in prod.py)
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SECURE_HSTS_SECONDS = 0
SECURE_SSL_REDIRECT = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
}

# Jazzmin Admin UI
JAZZMIN_SETTINGS = {
    "site_title": "Gestion de Budget",
    "site_header": "Gestion de Budget",
    "site_brand": "Budget Admin",
    "welcome_sign": "Bienvenue sur l'administration",
    "copyright": "Gestion de Budget 2026",
    "search_model": ["auth.User", "budgets.InfosBudget"],
    "topmenu_links": [
        {"name": "Accueil", "url": "admin:index"},
        {"name": "Voir le site", "url": "/budgets/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        # Auth
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        # Budgets
        "budgets.InfosBudget": "fas fa-file-invoice-dollar",
        "budgets.Metier": "fas fa-hard-hat",
        "budgets.Localite": "fas fa-map-marker-alt",
        "budgets.GroupeArticle": "fas fa-layer-group",
        "budgets.LigneBudgetaire": "fas fa-stream",
        # Projects
        "projects.Project": "fas fa-project-diagram",
        "projects.AppelAProjet": "fas fa-bullhorn",
        # Operators
        "operators.Operator": "fas fa-building",
        # Conventions
        "conventions.Convention": "fas fa-file-signature",
        # Workflow
        "workflow.WorkflowEvent": "fas fa-exchange-alt",
        # Audits
        "audits.IntegrationEvent": "fas fa-plug",
        "audits.AuditLog": "fas fa-history",
        # Exports
        "exports.ExportJob": "fas fa-file-export",
        # Integrations
        "integrations.IntegrationHealth": "fas fa-heartbeat",
        "integrations.GoodGrantsApplication": "fas fa-hand-holding-usd",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    "changeform_format": "single",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark navbar-primary",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

# Email configuration - Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER', 'noreply@gestion-budget.local')

