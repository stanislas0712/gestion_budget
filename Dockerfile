FROM python:3.9-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV_TYPE=production \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

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
    bash \
    # Pour psycopg2
    musl-dev \
    # Pour PostGIS/GDAL (Django GIS) - nécessite le dépôt communautaire
    gdal \
    gdal-dev \
    geos \
    geos-dev \
    proj \
    proj-dev \
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



# Copie du script d'entrée AVANT de copier tout le reste
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Convertir les fins de ligne et rendre exécutable
RUN dos2unix /docker-entrypoint.sh 2>/dev/null || sed -i 's/\r$//' /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh && \
    # Vérifier que le fichier existe et est exécutable
    ls -la /docker-entrypoint.sh && \
    test -f /docker-entrypoint.sh && test -x /docker-entrypoint.sh

# Copie du reste du code
COPY . .

# S'assurer que le fichier d'entrée est toujours présent et exécutable après COPY . .
# et que bash est disponible
RUN test -f /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh && \
    which bash || (apk add --no-cache bash && which bash) && \
    echo "✅ docker-entrypoint.sh est prêt: $(ls -la /docker-entrypoint.sh)"

# Point d'entrée
ENTRYPOINT ["/docker-entrypoint.sh"]
