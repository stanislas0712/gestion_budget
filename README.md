## Plateforme Budget (GoodGrants → Django → Odoo)

Hub métier Django (auditables & sécurisé) entre **GoodGrants** (source des demandes validées) et **Odoo** (ERP exécution).

### Stack

- **Django 4.x**
- **PostgreSQL**
- **HTMX** (pas de SPA/React)
- Architecture modulaire: **apps** + **services** + **integrations**

### Structure

- `config/`: settings split + urls + asgi/wsgi
- `apps/`: bounded contexts (`integrations`, `operators`, `projects`, `conventions`, `budgets`, `workflow`, `audits`, `exports`)
- `templates/`: templates globaux (HTMX)

### Installation (dev)

Pré-requis: Python 3.10+ et PostgreSQL.

1) Créer un environnement virtuel et installer les dépendances:

```bash
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

2) Créer un fichier `.env` local (non versionné)

Copiez `env.example` vers `.env` et renseignez vos valeurs:
- `DJANGO_SECRET_KEY`
- `DB_*`
- `GOODGRANTS_*`
- `ODOO_*`

3) Lancer les migrations et démarrer:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Notes d’architecture (règles)

- Vues fines: la logique métier vit dans des **services** (ex: `apps/operators/services.py`)
- Intégrations séparées: `apps/integrations/goodgrants` et `apps/integrations/odoo`
- Traçabilité:
  - CRUD: `django-auditlog`
  - Historique: `django-simple-history`
  - Événements inter-systèmes: `apps.audits.IntegrationEvent`

### Settings

- Dev: `DJANGO_SETTINGS_MODULE=config.settings.dev`
- Prod: `DJANGO_SETTINGS_MODULE=config.settings.prod`

