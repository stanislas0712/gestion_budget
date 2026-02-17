# Documentation Complète - Plateforme de Gestion de Budget

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Structure du Projet](#structure-du-projet)
4. [Prérequis](#prérequis)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Lancement de l'Application](#lancement-de-lapplication)
8. [Fonctionnalités Principales](#fonctionnalités-principales)
9. [Modèles de Données](#modèles-de-données)
10. [URLs et Routes](#urls-et-routes)
11. [Intégrations](#intégrations)
12. [Dépannage](#dépannage)

---

## 🎯 Vue d'ensemble

**Plateforme Budget** est une application web Django conçue pour gérer le cycle de vie complet des budgets de projets de formation. Elle sert de hub métier entre **GoodGrants** (source des demandes validées) et **Odoo** (ERP d'exécution).

### Objectifs Principaux

- Gestion complète des budgets de projets de formation
- Workflow de validation (brouillon → soumis → approuvé/rejeté)
- Calculs automatiques des totaux et synthèses budgétaires
- Export des budgets en Excel, PDF et Word
- Intégration avec GoodGrants et Odoo
- Traçabilité complète avec audit et historique

### Stack Technologique

- **Backend**: Django 4.x
- **Base de données**: PostgreSQL
- **Frontend**: HTMX (pas de SPA/React)
- **Architecture**: Modulaire avec bounded contexts
- **Sécurité**: django-auditlog, django-simple-history
- **Export**: openpyxl, weasyprint, python-docx

---

## 🏗️ Architecture

### Architecture Modulaire

Le projet suit une architecture modulaire avec des **bounded contexts** séparés :

```
apps/
├── budgets/          # Gestion des budgets (cœur métier)
├── projects/         # Appels à projets et projets
├── operators/        # Gestion des opérateurs
├── conventions/     # Conventions de financement
├── integrations/    # Intégrations externes (GoodGrants, Odoo)
├── workflow/        # Gestion des workflows
├── audits/          # Audit et traçabilité
└── exports/         # Export de données
```

### Principes d'Architecture

1. **Vues fines**: La logique métier vit dans des **services** (ex: `apps/operators/services.py`)
2. **Intégrations séparées**: `apps/integrations/goodgrants` et `apps/integrations/odoo`
3. **Traçabilité**:
   - CRUD: `django-auditlog`
   - Historique: `django-simple-history`
   - Événements inter-systèmes: `apps.audits.IntegrationEvent`

---

## 📁 Structure du Projet

```
budget/
├── apps/                    # Applications Django modulaires
│   ├── audits/              # Audit et logs d'intégration
│   ├── budgets/             # Gestion des budgets (principal)
│   │   ├── models.py       # Modèles de données
│   │   ├── views.py        # Vues et contrôleurs
│   │   ├── urls.py         # Routes de l'application
│   │   ├── forms.py        # Formulaires
│   │   ├── services/       # Services métier
│   │   ├── templates/      # Templates HTML
│   │   └── management/     # Commandes de gestion
│   ├── conventions/         # Conventions de financement
│   ├── exports/            # Export de données
│   ├── integrations/       # Intégrations externes
│   │   ├── goodgrants/    # Intégration GoodGrants
│   │   └── odoo/          # Intégration Odoo
│   ├── operators/          # Gestion des opérateurs
│   ├── projects/           # Appels à projets
│   └── workflow/           # Workflow de validation
├── config/                  # Configuration Django
│   ├── settings/
│   │   ├── base.py        # Configuration de base
│   │   ├── dev.py         # Configuration développement
│   │   └── prod.py        # Configuration production
│   ├── urls.py            # URLs principales
│   ├── wsgi.py            # WSGI pour déploiement
│   └── asgi.py            # ASGI pour déploiement
├── templates/              # Templates globaux
│   ├── base.html          # Template de base
│   └── registration/      # Templates d'authentification
├── static/                 # Fichiers statiques (CSS, JS, images)
├── manage.py              # Script de gestion Django
├── requirements.txt       # Dépendances Python
├── security.env           # Variables d'environnement (à configurer)
└── README.md              # Documentation rapide
```

---

## 📦 Prérequis

### Logiciels Requis

- **Python**: 3.10 ou supérieur
- **PostgreSQL**: 12 ou supérieur
- **pip**: Gestionnaire de paquets Python
- **Git**: Pour le contrôle de version (optionnel)

### Vérification des Prérequis

```bash
# Vérifier Python
python --version
# Doit afficher Python 3.10.x ou supérieur

# Vérifier PostgreSQL
psql --version
# Doit afficher PostgreSQL 12.x ou supérieur
```

---

## 🚀 Installation

### Étape 1: Cloner le Projet (si applicable)

```bash
cd D:\Documents\luxdev\code\budget
```

### Étape 2: Créer un Environnement Virtuel

**Sur Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

**Sur Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Étape 3: Installer les Dépendances

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Étape 4: Créer la Base de Données PostgreSQL

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la base de données et l'utilisateur
CREATE DATABASE budget;
CREATE USER budget WITH PASSWORD 'budget';
ALTER ROLE budget SET client_encoding TO 'utf8';
ALTER ROLE budget SET default_transaction_isolation TO 'read committed';
ALTER ROLE budget SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE budget TO budget;
\q
```

---

## ⚙️ Configuration

### Configuration des Variables d'Environnement

Le fichier `security.env` contient toutes les variables d'environnement nécessaires. **Modifiez ce fichier** avec vos valeurs :

```env
# Django
DJANGO_SETTINGS_MODULE=config.settings.dev
DJANGO_SECRET_KEY=votre-cle-secrete-ici
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données PostgreSQL
DB_NAME=budget
DB_USER=budget
DB_PASSWORD=votre-mot-de-passe
DB_HOST=localhost
DB_PORT=5432

# Intégrations GoodGrants
GOODGRANTS_API_BASE_URL=https://benkadibaara.grantplatform.com/api-key
GOODGRANTS_API_TOKEN=votre-token-ici

# Intégrations Odoo
ODOO_API_BASE_URL=https://votre-odoo.com
ODOO_API_DB=votre-base-odoo
ODOO_API_USERNAME=votre-utilisateur
ODOO_API_PASSWORD=votre-mot-de-passe

# Email Gmail SMTP
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
```

### Génération d'une Clé Secrète Django

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copiez la clé générée dans `DJANGO_SECRET_KEY` du fichier `security.env`.

---

## 🎬 Lancement de l'Application

### Étape 1: Appliquer les Migrations

```bash
# Créer les migrations (si nécessaire)
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate
```

### Étape 2: Créer un Superutilisateur

```bash
python manage.py createsuperuser
```

Suivez les instructions pour créer un compte administrateur :
- Nom d'utilisateur
- Email (optionnel)
- Mot de passe

### Étape 3: Collecter les Fichiers Statiques (optionnel)

```bash
python manage.py collectstatic --noinput
```

### Étape 4: Lancer le Serveur de Développement

```bash
python manage.py runserver
```

L'application sera accessible à l'adresse : **http://127.0.0.1:8000/**

### Étape 5: Accéder à l'Application

- **Interface utilisateur**: http://127.0.0.1:8000/
- **Interface d'administration**: http://127.0.0.1:8000/manager/

---

## 🎯 Fonctionnalités Principales

### 1. Gestion des Budgets

#### Création d'un Budget

1. Se connecter en tant qu'opérateur (pas d'admin)
2. Accéder au tableau de bord
3. Cliquer sur "Créer un budget"
4. Remplir les informations :
   - Appel à projet (doit être actif)
   - Opérateur/Consortium
   - Titre du projet
   - Filière, Métier, Localité
   - Nombre d'apprenants
   - Nombre de sessions

#### Structure Budgétaire

Un budget est automatiquement initialisé avec la structure suivante :

- **Section A - Formation**
  - **A.1 - Matières d'œuvre**
    - Intrants et/ou matières premières
    - Petites Fournitures Pédagogiques
  - **A.2 - Coûts pédagogiques**
    - Frais pédagogiques
    - Honoraires
    - Rapportage
    - Prise en charge des apprenants

- **Section B - Accompagnement à l'insertion**
  - Activités d'appui à l'insertion

#### Ajout d'Articles

1. Cliquer sur "Ajouter une ligne" dans un groupe
2. Remplir :
   - Désignation
   - Unité
   - Quantité
   - Prix unitaire
   - Co-financement
3. Les totaux sont calculés automatiquement

#### Calculs Automatiques

- **Coût total article** = Quantité × Prix unitaire
- **Budget demandé article** = Coût total - Co-financement
- Les totaux remontent automatiquement : Article → Groupe → Ligne → Section → Budget global

#### Règle de Validation A.1

La ligne A.1 ne peut pas dépasser **30% du budget total**. Une alerte s'affiche si cette règle n'est pas respectée.

### 2. Workflow de Validation

#### Statuts d'un Budget

1. **Brouillon**: Budget en cours de création
2. **Soumis**: Budget soumis pour validation
3. **Demande de modification**: L'admin demande des modifications
4. **Modification autorisée**: L'opérateur peut modifier
5. **Approuvé**: Budget validé par l'admin
6. **Rejeté**: Budget rejeté par l'admin

#### Soumission d'un Budget

1. L'opérateur clique sur "Soumettre le budget"
2. Le système vérifie :
   - Que le budget est modifiable
   - Que la règle des 30% pour A.1 est respectée
3. Un email est envoyé à l'admin

#### Actions Administrateur

- **Approuver**: Valide définitivement le budget
- **Demander modification**: Demande des modifications avec motif
- **Rejeter**: Rejette le budget

### 3. Export de Budgets

Les administrateurs peuvent exporter les budgets en :

- **Excel** (`.xlsx`): Format tableur avec mise en forme
- **PDF** (`.pdf`): Document imprimable
- **Word** (`.docx`): Document éditable

### 4. Gestion des Utilisateurs

#### Inscription d'un Opérateur

1. Accéder à `/accounts/inscription/`
2. Remplir le formulaire :
   - Nom d'utilisateur
   - Prénom
   - Nom
   - Email
   - Mot de passe
3. Le compte est créé avec les droits d'opérateur (pas admin)

#### Gestion du Profil

- Consulter son profil
- Changer son mot de passe

### 5. Recherche et Filtres

Le tableau de bord permet de :
- Rechercher par titre, opérateur, filière, localité, métier
- Filtrer par appel à projet
- Filtrer par filière
- Filtrer par localité

---

## 💾 Modèles de Données

### Modèle Principal: InfosBudget

```python
InfosBudget
├── uuid (UUID unique)
├── appel_a_projet (ForeignKey)
├── created_by (ForeignKey User)
├── operateur (CharField)
├── titre_projet (TextField)
├── filiere (ForeignKey Filiere)
├── metier (ForeignKey Metier)
├── localite (ForeignKey Localite)
├── total_apprenants (PositiveIntegerField)
├── nombre_sessions (PositiveIntegerField)
├── statut (CharField avec choix)
├── Totaux calculés:
│   ├── cout_total_global
│   ├── co_financement_global
│   ├── budget_demande_global
│   ├── cout_par_apprenant
│   ├── apprenants_par_session
│   ├── cout_par_session
│   └── pourcentage_a1
└── Historique (django-simple-history)
```

### Hiérarchie Budgétaire

```
InfosBudget (Budget)
└── SectionBudgetaire (A, B)
    └── LigneBudgetaire (A.1, A.2, B)
        └── GroupeArticle (Intrants, Honoraires, etc.)
            └── SousLigneArticle (Articles individuels)
```

### Modèles de Référence

- **Metier**: Métiers de formation
- **Filiere**: Filières de formation
- **Localite**: Localités géographiques
- **AppelAProjet**: Appels à projets avec dates
- **Operator**: Opérateurs/consortiums
- **Project**: Projets liés à GoodGrants

---

## 🔗 URLs et Routes

### Routes Principales

```
/                           → Redirection vers login
/accounts/login/            → Connexion
/accounts/logout/           → Déconnexion
/accounts/inscription/      → Inscription opérateur
/budgets/                   → Tableau de bord
/budgets/creer/             → Créer un budget
/budgets/<uuid>/            → Détail d'un budget
/budgets/<uuid>/modifier/   → Modifier un budget
/budgets/<uuid>/soumettre/  → Soumettre un budget
/budgets/<uuid>/approuver/  → Approuver (admin)
/budgets/<uuid>/rejeter/    → Rejeter (admin)
/budgets/export-excel/<uuid>/ → Export Excel
/budgets/export-pdf/<uuid>/   → Export PDF
/budgets/export-word/<uuid>/  → Export Word
/manager/                   → Interface d'administration Django
```

### Routes HTMX (AJAX)

```
/budgets/ajouter-ligne/<groupe_id>/      → Formulaire d'ajout
/budgets/sauvegarder-ligne/<groupe_id>/  → Sauvegarde article
/budgets/supprimer-article/<article_id>/ → Suppression article
/budgets/get-synthese/<uuid>/            → Rafraîchir synthèse
/budgets/get-statut/<uuid>/              → Statut du budget
/budgets/get-pourcentage-a1/<uuid>/      → Pourcentage A.1
```

---

## 🔌 Intégrations

### Intégration GoodGrants

- **Objectif**: Récupérer les demandes validées depuis GoodGrants
- **Configuration**: Variables `GOODGRANTS_API_*` dans `security.env`
- **Services**: `apps/integrations/goodgrants/services.py`

### Intégration Odoo

- **Objectif**: Synchroniser les budgets approuvés vers Odoo
- **Configuration**: Variables `ODOO_API_*` dans `security.env`
- **Services**: `apps/integrations/odoo/services.py`

### Santé des Intégrations

Le modèle `IntegrationHealth` suit l'état des intégrations :
- Dernière synchronisation réussie
- Dernière erreur
- Message d'erreur

---

## 🛠️ Dépannage

### Problème: Erreur de connexion à la base de données

**Solution:**
1. Vérifier que PostgreSQL est démarré
2. Vérifier les identifiants dans `security.env`
3. Vérifier que la base de données existe :
   ```bash
   psql -U budget -d budget -c "SELECT 1;"
   ```

### Problème: Migrations en erreur

**Solution:**
```bash
# Voir l'état des migrations
python manage.py showmigrations

# Appliquer les migrations manquantes
python manage.py migrate

# Si nécessaire, réinitialiser (ATTENTION: perte de données)
python manage.py migrate --run-syncdb
```

### Problème: Erreur "Module not found"

**Solution:**
1. Vérifier que l'environnement virtuel est activé
2. Réinstaller les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

### Problème: Erreur d'email

**Solution:**
1. Vérifier les identifiants Gmail dans `security.env`
2. Utiliser un "Mot de passe d'application" Gmail (pas le mot de passe normal)
3. Activer l'authentification à 2 facteurs sur Gmail

### Problème: Les totaux ne se calculent pas

**Solution:**
1. Forcer le recalcul :
   ```python
   from apps.budgets.models import InfosBudget
   budget = InfosBudget.objects.get(uuid='...')
   budget.calculer_synthese()
   ```

### Problème: Accès refusé

**Solution:**
1. Vérifier que vous êtes connecté
2. Vérifier vos droits (opérateur vs admin)
3. Vérifier que le budget vous appartient (pour les opérateurs)

---

## 📝 Commandes Utiles

### Commandes Django

```bash
# Créer un superutilisateur
python manage.py createsuperuser

# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Lancer le serveur
python manage.py runserver

# Lancer le serveur sur un port spécifique
python manage.py runserver 8080

# Collecter les fichiers statiques
python manage.py collectstatic

# Ouvrir le shell Django
python manage.py shell

# Créer un utilisateur (commande personnalisée)
python manage.py creer_utilisateur
```

### Commandes PostgreSQL

```bash
# Se connecter à la base
psql -U budget -d budget

# Lister les tables
\dt

# Voir la structure d'une table
\d budgets_infosbudget

# Exécuter une requête SQL
SELECT * FROM budgets_infosbudget LIMIT 10;
```

---

## 🔒 Sécurité

### Bonnes Pratiques

1. **Ne jamais commiter `security.env`** dans Git
2. Utiliser des mots de passe forts en production
3. Changer `DJANGO_SECRET_KEY` en production
4. Configurer `ALLOWED_HOSTS` correctement
5. Activer HTTPS en production
6. Utiliser des variables d'environnement pour les secrets

### Configuration Production

Le fichier `config/settings/prod.py` active :
- HTTPS obligatoire
- Cookies sécurisés
- HSTS (HTTP Strict Transport Security)

---

## 📚 Ressources Supplémentaires

### Documentation Django

- [Documentation Django](https://docs.djangoproject.com/)
- [Django HTMX](https://django-htmx.readthedocs.io/)
- [Django Simple History](https://django-simple-history.readthedocs.io/)

### Packages Utilisés

- `django-auditlog`: Audit des modifications
- `django-simple-history`: Historique des changements
- `django-htmx`: Interactions AJAX
- `openpyxl`: Export Excel
- `weasyprint`: Export PDF
- `python-docx`: Export Word

---

## 📞 Support

Pour toute question ou problème :

1. Consulter cette documentation
2. Vérifier les logs Django
3. Vérifier les logs PostgreSQL
4. Consulter la documentation Django officielle

---

**Dernière mise à jour**: 2024
**Version**: 1.0
