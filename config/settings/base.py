from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

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

# Database (PostgreSQL by default; configure via env vars)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "budget"),
        "USER": os.environ.get("DB_USER", "budget"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "budget"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
    }
}

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

