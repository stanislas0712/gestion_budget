from auditlog.registry import auditlog
from django.contrib import admin

from .models import Project, AppelAProjet


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "operator", "status", "ready_for_convention", "validated_by_admin", "updated_at")
    list_filter = ("status", "ready_for_convention", "validated_by_admin")
    search_fields = ("title", "operator__name", "gg_application__gg_id")
    raw_id_fields = ("gg_application", "operator")
    readonly_fields = ("created_at", "updated_at", "validated_at", "locked_at")
    fieldsets = (
        ('Informations Générales', {
            'classes': ('wide',),
            'fields': ('title', 'operator', 'gg_application', 'sector', 'locations'),
        }),
        ('Budget & Statut', {
            'classes': ('wide',),
            'fields': ('approved_budget', 'status', 'ready_for_convention'),
        }),
        ('Validation Admin', {
            'classes': ('wide',),
            'fields': ('validated_by_admin', 'admin_comment', 'validated_at', 'locked_at'),
        }),
        ('Dates', {
            'classes': ('wide',),
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(AppelAProjet)
class AppelAProjetAdmin(admin.ModelAdmin):
    list_display = ("nom", "date_debut", "date_fin", "est_actif", "created_by")
    list_filter = ("date_debut", "date_fin")
    search_fields = ("nom",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ('Informations', {
            'classes': ('wide',),
            'fields': ('nom', 'created_by'),
        }),
        ('Période', {
            'classes': ('wide',),
            'fields': ('date_debut', 'date_fin'),
        }),
        ('Dates système', {
            'classes': ('wide',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def est_actif(self, obj):
        return obj.est_actif
    est_actif.boolean = True
    est_actif.short_description = "Actif"


auditlog.register(Project)
auditlog.register(AppelAProjet)

