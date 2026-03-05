from auditlog.registry import auditlog
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import ExportJob


@admin.register(ExportJob)
class ExportJobAdmin(SimpleHistoryAdmin):
    list_display = ("kind", "status", "created_by", "created_at", "updated_at")
    list_filter = ("kind", "status")
    search_fields = ("error_message",)
    list_per_page = 10
    history_list_per_page = 10
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ('Type & Statut', {
            'classes': ('wide',),
            'fields': ('kind', 'status'),
        }),
        ('Paramètres & Résultat', {
            'classes': ('wide',),
            'fields': ('parameters', 'result_file', 'error_message'),
        }),
        ('Métadonnées', {
            'classes': ('wide',),
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )


auditlog.register(ExportJob)

