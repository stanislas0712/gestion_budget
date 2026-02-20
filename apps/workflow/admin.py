from auditlog.registry import auditlog
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import WorkflowEvent


@admin.register(WorkflowEvent)
class WorkflowEventAdmin(SimpleHistoryAdmin):
    list_display = ("action", "content_type", "object_id", "created_by", "created_at")
    list_filter = ("action", "content_type")
    search_fields = ("object_id", "notes")
    list_per_page = 10
    history_list_per_page = 10
    readonly_fields = ("created_at",)
    fieldsets = (
        ('Objet concerné', {
            'classes': ('wide',),
            'fields': ('content_type', 'object_id'),
        }),
        ('Action & Détails', {
            'classes': ('wide',),
            'fields': ('action', 'notes'),
        }),
        ('Métadonnées', {
            'classes': ('wide',),
            'fields': ('created_by', 'created_at'),
        }),
    )


auditlog.register(WorkflowEvent)

