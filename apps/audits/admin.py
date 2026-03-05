from auditlog.registry import auditlog
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import IntegrationEvent, AuditLog

# Note: Personnalisation de l'admin LogEntry désactivée car l'API de django-auditlog a changé
# Si nécessaire, on peut personnaliser via les settings d'auditlog


@admin.register(IntegrationEvent)
class IntegrationEventAdmin(SimpleHistoryAdmin):
    list_display = ("system", "direction", "status", "external_id", "correlation_id", "created_at")
    list_filter = ("system", "direction", "status")
    search_fields = ("external_id", "correlation_id", "error_message")
    readonly_fields = ("created_at",)
    list_per_page = 10
    history_list_per_page = 10
    fieldsets = (
        ('Identification', {
            'classes': ('wide',),
            'fields': ('system', 'direction', 'status'),
        }),
        ('Références Externes', {
            'classes': ('wide',),
            'fields': ('correlation_id', 'external_id'),
        }),
        ('Données échangées', {
            'classes': ('wide',),
            'fields': ('request_payload', 'response_payload', 'error_message'),
        }),
        ('Métadonnées', {
            'classes': ('wide',),
            'fields': ('created_by', 'created_at'),
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(SimpleHistoryAdmin):
    list_display = ("action", "model_name", "object_id", "user", "created_at")
    list_filter = ("action", "model_name")
    search_fields = ("model_name", "object_id", "user__username")
    readonly_fields = ("created_at",)
    list_per_page = 10
    history_list_per_page = 10
    fieldsets = (
        ('Action', {
            'classes': ('wide',),
            'fields': ('action', 'model_name', 'object_id'),
        }),
        ('Détails des changements', {
            'classes': ('wide',),
            'fields': ('changes', 'metadata'),
        }),
        ('Utilisateur & Contexte', {
            'classes': ('wide',),
            'fields': ('user', 'ip_address', 'user_agent'),
        }),
        ('Date', {
            'classes': ('wide',),
            'fields': ('created_at',),
        }),
    )


auditlog.register(IntegrationEvent)
auditlog.register(AuditLog)

