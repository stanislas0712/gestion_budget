from auditlog.registry import auditlog
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Convention


@admin.register(Convention)
class ConventionAdmin(SimpleHistoryAdmin):
<<<<<<< HEAD
    list_display = ("reference", "project", "budget", "date_signature", "get_montant", "get_cofinancement", "status", "odoo_id", "updated_at")
=======
    list_display = ("reference", "project", "status", "odoo_id", "updated_at")
>>>>>>> 052578e1e8b11c61f5334ebd3f068aefcfadd3b2
    list_filter = ("status",)
    search_fields = ("reference", "project__title", "project__operator__name")
    list_per_page = 10
    history_list_per_page = 10
<<<<<<< HEAD
    raw_id_fields = ("project", "budget")
    readonly_fields = ("get_montant", "get_cofinancement", "created_at", "updated_at", "validated_at", "sent_to_odoo_at")
    fieldsets = (
        ('Informations Générales', {
            'classes': ('wide',),
            'fields': ('reference', 'date_signature', 'project', 'budget'),
        }),
        ('Montants (issus du budget)', {
            'classes': ('wide',),
            'fields': ('get_montant', 'get_cofinancement'),
=======
    raw_id_fields = ("project",)
    readonly_fields = ("created_at", "updated_at", "validated_at", "sent_to_odoo_at")
    fieldsets = (
        ('Informations Générales', {
            'classes': ('wide',),
            'fields': ('reference', 'project'),
>>>>>>> 052578e1e8b11c61f5334ebd3f068aefcfadd3b2
        }),
        ('Période', {
            'classes': ('wide',),
            'fields': ('start_date', 'end_date'),
        }),
        ('Statut & Validation', {
            'classes': ('wide',),
            'fields': ('status', 'validated_at'),
        }),
        ('Intégration Odoo', {
            'classes': ('wide',),
            'fields': ('odoo_id', 'sent_to_odoo_at'),
        }),
        ('Dates système', {
            'classes': ('wide',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

<<<<<<< HEAD
    @admin.display(description="Montant convention")
    def get_montant(self, obj):
        return obj.montant

    @admin.display(description="Cofinancement")
    def get_cofinancement(self, obj):
        return obj.cofinancement

=======
>>>>>>> 052578e1e8b11c61f5334ebd3f068aefcfadd3b2

auditlog.register(Convention)

