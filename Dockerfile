FROM python:3.9-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV_TYPE=production \
    PYTHONPATH=/app

# Installation des dépendances système
RUN apk add --no-cache \
    postgresql-client \
    redis \
    jpeg-dev \
    zlib-dev \
    libwebp-dev \
    libpng-dev \
    tiff-dev \
    openjpeg-dev \
    freetype-dev \
    lcms2-dev \
    netcat-openbsd \
    postgresql-dev \
    curl \
    build-base \
    dos2unix \
    # Pour psycopg2
    musl-dev \
    # Pour Pillow
    jpeg-dev \
    && pip install --no-cache-dir --upgrade pip


# Création du répertoire de travail
WORKDIR /app


RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    mkdir -p /dev/shm && \
    chown -R 777 /app


# Copie du fichier requirements pour installer les dépendances
COPY requirements.txt .


# Installation des dépendances Python dans un virtualenv
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt



COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh && \
    # Convertir les fins de ligne Windows en Unix si nécessaire
    sed -i 's/\r$//' /docker-entrypoint.sh

COPY . .

# Point d'entrée
ENTRYPOINT ["/docker-entrypoint.sh"]
