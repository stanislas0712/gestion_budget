from auditlog.registry import auditlog
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import IntegrationHealth
from .goodgrants.models import GoodGrantsApplication


@admin.register(IntegrationHealth)
class IntegrationHealthAdmin(admin.ModelAdmin):
    list_display = ("system", "last_success_at", "last_error_at", "updated_at")
    search_fields = ("system",)
    list_per_page = 10
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ('Système', {
            'classes': ('wide',),
            'fields': ('system',),
        }),
        ('État de santé', {
            'classes': ('wide',),
            'fields': ('last_success_at', 'last_error_at', 'last_error_message'),
        }),
        ('Dates système', {
            'classes': ('wide',),
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(GoodGrantsApplication)
class GoodGrantsApplicationAdmin(SimpleHistoryAdmin):
    list_display = ("gg_id", "status", "validated_at", "synced", "synced_at", "received_at")
    list_filter = ("status", "synced")
    search_fields = ("gg_id",)
    list_per_page = 10
    history_list_per_page = 10
    readonly_fields = ("received_at", "updated_at", "raw_payload")
    fieldsets = (
        ('Identification', {
            'classes': ('wide',),
            'fields': ('gg_id', 'status'),
        }),
        ('Validation', {
            'classes': ('wide',),
            'fields': ('validated_at',),
        }),
        ('Synchronisation', {
            'classes': ('wide',),
            'fields': ('synced', 'synced_at'),
        }),
        ('Données brutes & Dates', {
            'classes': ('wide',),
            'fields': ('raw_payload', 'received_at', 'updated_at'),
        }),
    )


auditlog.register(IntegrationHealth)
auditlog.register(GoodGrantsApplication)

