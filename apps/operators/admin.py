from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin
from .models import Operator

@admin.register(Operator)
class OperatorAdmin(SimpleHistoryAdmin):
   
    list_display = [
        'name',
        'type_badge',
        'status_badge',
        'is_verified',
        'city',
        'country',
        'odoo_sync_status',
        'created_at',
    ]
    
   
    list_filter = [
        'type',
        'status',
        'is_verified',
        'country',
    ]
    
    search_fields = ['name', 'registration_number', 'gg_operator_id']
    list_per_page = 10
    history_list_per_page = 10
    
    readonly_fields = [
        'gg_operator_id',
        'odoo_partner_id',
        'created_at',
        'updated_at',
        'verified_at',
    ]

    fieldsets = (
        ('Identité', {
            'classes': ('wide',),
            'fields': ('name', 'legal_name', 'acronym', 'type', 'registration_number'),
        }),
        ('Statut & Vérification', {
            'classes': ('wide',),
            'fields': ('status', 'is_verified', 'verified_at'),
        }),
        ('Coordonnées', {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'address', 'city', 'country'),
        }),
        ('Intégrations Externes', {
            'classes': ('wide',),
            'fields': ('gg_operator_id', 'odoo_partner_id'),
        }),
        ('Données brutes & Métadonnées', {
            'classes': ('wide',),
            'fields': ('raw_data', 'created_by', 'created_at', 'updated_at'),
        }),
    )

    # --- Méthodes pour les badges ---
    def type_badge(self, obj):
        colors = {'ngo': 'primary', 'association': 'info', 'company': 'warning'}
        color = colors.get(obj.type, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_type_display())
    type_badge.short_description = 'Type'

    def status_badge(self, obj):
        colors = {'active': 'success', 'inactive': 'secondary', 'suspended': 'danger'}
        color = colors.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Statut'

    def odoo_sync_status(self, obj):
        if obj.odoo_partner_id:
            return format_html('<span class="badge bg-success">Synchronisé</span>')
        return format_html('<span class="badge bg-warning">Non sync</span>')
    odoo_sync_status.short_description = 'Odoo'