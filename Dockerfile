# ============================================
# Stage 1: Builder - Installation des dépendances
# ============================================
FROM python:3.11-alpine AS builder

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installation des dépendances système nécessaires pour la compilation
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    postgresql-dev \
    python3-dev \
    jpeg-dev \
    zlib-dev \
    libwebp-dev \
    libpng-dev \
    tiff-dev \
    openjpeg-dev \
    freetype-dev \
    lcms2-dev \
    && pip install --no-cache-dir --upgrade pip

# Création du répertoire de travail
WORKDIR /app

# Copie du fichier requirements pour installer les dépendances
COPY requirements.txt .

# Installation des dépendances Python dans un virtualenv
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# Nettoyer les dépendances de build pour réduire la taille
RUN apk del .build-deps

# ============================================
# Stage 2: Runtime - Image finale optimisée
# ============================================
FROM python:3.11-alpine

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod

# Installation des dépendances système minimales pour l'exécution
RUN apk add --no-cache \
    postgresql-client \
    libpq \
    curl \
    bash \
    # Dépendances pour weasyprint (PDF)
    pango \
    cairo \
    gdk-pixbuf \
    fontconfig \
    shared-mime-info \
    # Dépendances runtime pour les bibliothèques Python
    jpeg \
    zlib \
    libwebp \
    libpng \
    tiff \
    openjpeg \
    freetype \
    lcms2

# Copie du virtualenv depuis le stage builder
COPY --from=builder /opt/venv /opt/venv

# Création d'un utilisateur non-root pour la sécurité (Alpine utilise addgroup/adduser)
RUN addgroup -S django && adduser -S django -G django

# Création des répertoires nécessaires
WORKDIR /app
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    mkdir -p /dev/shm && \
    chown -R django:django /app

# Copie du code de l'application
COPY --chown=django:django . .

# Script d'entrée (copier avant de changer d'utilisateur pour éviter les problèmes de permissions)
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && \
    # Convertir les fins de ligne Windows en Unix si nécessaire
    sed -i 's/\r$//' /docker-entrypoint.sh

# Utilisateur non-root
USER django

# Exposition du port
EXPOSE 8000

# Point d'entrée
ENTRYPOINT ["/docker-entrypoint.sh"]
