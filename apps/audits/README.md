# App Audits - Documentation Complète

## Vue d'ensemble

L'application **audits** est le système central de traçabilité et d'audit de la plateforme Budget. Elle assure la traçabilité complète de toutes les opérations, en particulier les échanges entre systèmes (GoodGrants ↔ Django ↔ Odoo).

## Fonctionnalités

### 1. IntegrationEvent
Traçabilité des événements inter-systèmes :
- Synchronisations GoodGrants → Django
- Créations/Mises à jour Django → Odoo
- Webhooks GoodGrants
- Gestion des erreurs et retry automatique

### 2. AuditLog  
Logs d'audit des actions utilisateurs :
- Créations, modifications, suppressions
- Approbations et rejets
- Exports et imports
- Capture IP, User Agent, changements avant/après

## Structure de l'app

```
apps/audits/
├── __init__.py              # Package init
├── apps.py                  # Configuration Django app
├── models.py                # IntegrationEvent, AuditLog
├── admin.py                 # Interface d'administration
├── services.py              # Logique métier
│   ├── IntegrationEventService
│   ├── AuditLogService
│   └── IntegrationContextManager
├── views.py                 # Vues HTMX
│   ├── DashboardView
│   ├── IntegrationEventListView
│   ├── IntegrationEventDetailView
│   ├── AuditLogListView
│   └── AuditLogDetailView
├── urls.py                  # Routing
└── tests.py                 # Tests complets
```

## Modèles de données

### IntegrationEvent

```python
class IntegrationEvent(models.Model):
    # Type d'événement
    event_type = CharField(choices=EventType.choices)
    
    # Statut
    status = CharField(choices=Status.choices)
    
    # Systèmes
    source_system = CharField()  # goodgrants, django, odoo
    destination_system = CharField()
    
    # Références
    external_id = CharField()  # ID dans système externe
    internal_id = CharField()  # ID dans Django
    
    # Données
    request_data = JSONField()   # Payload requête
    response_data = JSONField()  # Payload réponse
    error_message = TextField()
    error_traceback = TextField()
    
    # Métadonnées
    duration_ms = IntegerField()
    retry_count = IntegerField()
    
    # Timestamps
    created_at = DateTimeField()
    updated_at = DateTimeField()
    completed_at = DateTimeField()
```

**Statuts** :
- `SUCCESS` : Opération réussie
- `FAILED` : Échec
- `PENDING` : En cours
- `RETRY` : Nouvelle tentative

**Types d'événements** :
- `GOODGRANTS_SYNC` : Synchronisation depuis GoodGrants
- `GOODGRANTS_WEBHOOK` : Webhook reçu de GoodGrants
- `ODOO_SYNC` : Synchronisation vers Odoo
- `ODOO_CREATE` : Création dans Odoo
- `ODOO_UPDATE` : Mise à jour Odoo
- `ERROR` : Erreur générique

### AuditLog

```python
class AuditLog(models.Model):
    # Action
    action = CharField(choices=Action.choices)
    model_name = CharField()
    object_id = CharField()
    
    # Données
    changes = JSONField()  # {"before": {...}, "after": {...}}
    metadata = JSONField()
    
    # Utilisateur
    user = ForeignKey(User)
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    
    # Timestamp
    created_at = DateTimeField()
```

**Actions** :
- `CREATE` : Création
- `UPDATE` : Modification
- `DELETE` : Suppression
- `APPROVE` : Approbation
- `REJECT` : Rejet
- `EXPORT` : Export
- `IMPORT` : Import

## 🔧 Services

### IntegrationEventService

#### Méthodes principales

```python
# Créer un événement
event = IntegrationEventService.create_event(
    event_type=IntegrationEvent.EventType.GOODGRANTS_SYNC,
    source_system='goodgrants',
    destination_system='django',
    external_id='GG-123',
    request_data=payload,
    user=request.user
)

# Marquer comme succès
IntegrationEventService.mark_success(
    event,
    response_data={'id': 42},
    duration_ms=150
)

# Marquer comme échec
IntegrationEventService.mark_failed(
    event,
    error=exception,
    include_traceback=True
)

# Obtenir les événements récents
events = IntegrationEventService.get_recent_events(
    limit=100,
    event_type='goodgrants_sync',
    status='failed'
)

# Statistiques
stats = IntegrationEventService.get_statistics(
    start_date=datetime.now() - timedelta(days=7)
)
# Retourne: {total, success, failed, pending, avg_duration, success_rate}
```

### AuditLogService

#### Méthodes principales

```python
# Logger une action générique
AuditLogService.log_action(
    action=AuditLog.Action.UPDATE,
    model_name='Project',
    object_id='123',
    user=request.user,
    changes={'before': {...}, 'after': {...}},
    request=request  # Capture IP et User Agent
)

# Méthodes raccourcies
AuditLogService.log_create('Project', '123', user=user)
AuditLogService.log_update('Project', '123', changes={...}, user=user)
AuditLogService.log_delete('Project', '123', user=user)

# Historique d'un objet
history = AuditLogService.get_object_history('Project', '123')

# Activité d'un utilisateur
activity = AuditLogService.get_user_activity(user, limit=50)
```

### IntegrationContextManager

**Context manager** pour tracker automatiquement les intégrations :

```python
# Utilisation
with IntegrationContextManager(
    event_type=IntegrationEvent.EventType.ODOO_CREATE,
    source_system='django',
    destination_system='odoo',
    external_id=operator.gg_operator_id,
    request_data={'name': operator.name}
) as event:
    # Faire le travail d'intégration
    partner_id = odoo_client.create_partner(data)
    
    # Stocker la réponse
    event.response_data = {'partner_id': partner_id}
    
# Si tout se passe bien → SUCCESS automatique
# Si exception → FAILED automatique avec traceback
```

## Vues et Templates

### Dashboard (`/audits/`)
- Statistiques 24h, 7j, 30j
- Événements en échec (besoin d'attention)
- Événements récents
- Logs d'audit récents
- Graphiques par type et statut

### Liste des événements (`/audits/events/`)
- Filtres : type, statut, système, recherche
- Pagination
- Statistiques résumées

### Détail d'un événement (`/audits/events/<id>/`)
- Informations complètes
- Request/Response data (JSON formaté)
- Traceback d'erreur si échec
- Timeline

### Liste des logs (`/audits/logs/`)
- Filtres : action, modèle, utilisateur
- Recherche
- Pagination

### Détail d'un log (`/audits/logs/<id>/`)
- Changements avant/après
- Métadonnées
- Lien vers l'objet (si existant)

## Admin Django

Interface d'administration complète avec :

### IntegrationEventAdmin
- Liste avec badges colorés (type, statut)
- Filtres avancés
- JSON viewers pour request/response
- Traceback formaté
- Readonly (pas de création manuelle)
- Seul superuser peut supprimer

### AuditLogAdmin
- Liste avec badges
- Lien vers objet si possible
- JSON viewers
- Readonly complet
- Seul superuser peut supprimer

## Tests

Tests complets pytest avec :
- Modèles (création, mark_success, mark_failed, retry)
- Services (toutes les méthodes)
- Context manager (success et failure flows)
- Vues (dashboard, listes, détails)
- Coverage > 90%

### Lancer les tests

```bash
# Tous les tests de l'app audits
pytest apps/audits/tests.py -v

# Avec coverage
pytest apps/audits/tests.py --cov=apps.audits --cov-report=html

# Test spécifique
pytest apps/audits/tests.py::TestIntegrationEventService::test_create_event -v
```

## Exemples d'utilisation

### 1. Synchronisation GoodGrants

```python
from apps.audits.services import IntegrationContextManager
from apps.integrations.goodgrants.client import GoodGrantsClient
from apps.audits.models import IntegrationEvent

# Avec context manager (recommandé)
with IntegrationContextManager(
    event_type=IntegrationEvent.EventType.GOODGRANTS_SYNC,
    source_system='goodgrants',
    destination_system='django',
    external_id=gg_request_id,
    request_data={'gg_id': gg_request_id}
) as event:
    client = GoodGrantsClient()
    data = client.get_request_details(gg_request_id)
    
    # Créer le projet
    project = Project.objects.create(...)
    
    event.internal_id = str(project.id)
    event.response_data = {'project_id': project.id}
```

### 2. Push vers Odoo

```python
from apps.integrations.odoo.client import OdooClient
from apps.audits.services import IntegrationContextManager

def sync_operator_to_odoo(operator):
    with IntegrationContextManager(
        event_type=IntegrationEvent.EventType.ODOO_CREATE,
        source_system='django',
        destination_system='odoo',
        internal_id=str(operator.id),
        external_id=operator.gg_operator_id
    ) as event:
        client = OdooClient()
        partner_id = client.create_partner({
            'name': operator.name,
            'email': operator.email
        })
        
        operator.odoo_partner_id = partner_id
        operator.save()
        
        event.response_data = {'partner_id': partner_id}
```

### 3. Logger une action utilisateur

```python
from apps.audits.services import AuditLogService

def approve_project(project, user, request):
    old_status = project.status
    project.status = Project.Status.VALIDATED
    project.validated_by_admin = True
    project.validated_at = timezone.now()
    project.save()
    
    # Logger l'action
    AuditLogService.log_action(
        action=AuditLog.Action.APPROVE,
        model_name='Project',
        object_id=str(project.id),
        user=user,
        changes={
            'before': {'status': old_status},
            'after': {'status': project.status}
        },
        metadata={'comment': 'Approved by admin'},
        request=request
    )
```

##  Monitoring et Alerting

### Requêtes utiles

```python
# Événements en échec des dernières 24h
failed_events = IntegrationEvent.objects.filter(
    status=IntegrationEvent.Status.FAILED,
    created_at__gte=timezone.now() - timedelta(hours=24)
)

# Taux d'erreur par système
from django.db.models import Count, Q
stats = IntegrationEvent.objects.values('source_system').annotate(
    total=Count('id'),
    failed=Count('id', filter=Q(status='failed'))
)

# Événements lents (>5s)
slow_events = IntegrationEvent.objects.filter(
    duration_ms__gt=5000,
    created_at__gte=timezone.now() - timedelta(hours=24)
)

# Actions par utilisateur
from django.db.models import Count
user_stats = AuditLog.objects.values(
    'user__username'
).annotate(
    count=Count('id')
).order_by('-count')
```

## Intégration avec les autres apps

Toutes les autres apps utilisent `apps.audits` pour :

1. **Tracer les intégrations** : via `IntegrationContextManager`
2. **Logger les actions** : via `AuditLogService`
3. **Consulter l'historique** : via les méthodes de service

## Checklist de validation

- [x] Modèles créés et migrés
- [x] Admin interface configurée
- [x] Services implémentés
- [x] Context manager fonctionnel
- [x] Vues et templates HTMX
- [x] URLs configurées
- [x] Tests complets (>90% coverage)
- [x] Documentation complète

## Prochaines étapes

Maintenant que l'app `audits` est complète, nous pouvons passer aux autres apps dans cet ordre recommandé :

1.  **audits** (fait)
2. **integrations** - GoodGrants et Odoo clients
3. **operators** - Gestion des opérateurs
4. **projects** - Gestion des projets
5. **conventions** - Conventions de financement
6. **budgets** - Lignes budgétaires
7. **workflow** - Workflows de validation
8. **exports** - Génération d'exports

---

**App Audits** - Traçabilité complète et audit système
Version 1.0 - Budget Platform