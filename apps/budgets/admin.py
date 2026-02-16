from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    InfosBudget, SectionBudgetaire, LigneBudgetaire,
    GroupeArticle, SousLigneArticle, Metier, Localite, Filiere
)

# --- UTILISATEURS : toutes les sections visibles ---
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        ('Informations de connexion', {
            'classes': ('wide',),
            'fields': ('username', 'password'),
        }),
        ('Informations personnelles', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email'),
        }),
        ('Permissions', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Dates importantes', {
            'classes': ('wide',),
            'fields': ('last_login', 'date_joined'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_per_page = 10


@admin.register(Metier)
class MetierAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)
    list_per_page = 10


@admin.register(Localite)
class LocaliteAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)
    list_per_page = 10


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)
    list_per_page = 10

# --- NIVEAU BAS : ARTICLES DANS LES GROUPES ---

class SousLigneArticleInline(admin.TabularInline):
    model = SousLigneArticle
    extra = 1
    fields = ('designation', 'unite', 'quantite', 'prix_unitaire', 'co_financement', 'cout_total_article', 'budget_demande_article')
    readonly_fields = ('cout_total_article', 'budget_demande_article')

@admin.register(GroupeArticle)
class GroupeArticleAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'ligne', 'cout_total_groupe', 'budget_demande_groupe')
    inlines = [SousLigneArticleInline]
    list_filter = ('ligne__section__budget_parent',)
    list_per_page = 10

# --- NIVEAU MOYEN : GROUPES DANS LES LIGNES ---

class GroupeArticleInline(admin.TabularInline):
    model = GroupeArticle
    extra = 0
    fields = ('libelle', 'cout_total_groupe', 'co_financement_groupe', 'budget_demande_groupe')
    readonly_fields = fields # On ne modifie les montants que via les articles

@admin.register(LigneBudgetaire)
class LigneBudgetaireAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'section', 'cout_total_ligne')
    inlines = [GroupeArticleInline]
    list_per_page = 10

# --- NIVEAU HAUT : SECTIONS DANS LE BUDGET ---

class SectionBudgetaireInline(admin.StackedInline):
    model = SectionBudgetaire
    extra = 0
    readonly_fields = ('cout_total_section', 'co_financement_section', 'budget_demande_section')

@admin.register(InfosBudget)
class InfosBudgetAdmin(admin.ModelAdmin):
    """
    Vue principale du Budget
    """
    list_display = ('titre_projet', 'operateur', 'statut', 'cout_total_global', 'budget_demande_global', 'cout_par_apprenant', 'created_by')
    list_filter = ('statut', 'appel_a_projet', 'filiere', 'localite')
    search_fields = ('titre_projet', 'operateur', 'filiere__nom')
    list_per_page = 10
    fieldsets = (
        ('Informations Générales', {
            'classes': ('wide',),
            'fields': ('uuid', 'operateur', 'titre_projet', 'filiere', 'metier', 'localite', 'created_by', 'appel_a_projet'),
        }),
        ('Paramètres & Effectifs', {
            'classes': ('wide',),
            'fields': ('total_apprenants', 'nombre_sessions'),
        }),
        ('Workflow & Statut', {
            'classes': ('wide',),
            'fields': ('statut', 'date_soumission', 'date_approbation', 'motif_demande_modification', 'date_demande_modification', 'date_autorisation_modification'),
        }),
        ('Synthèse Financière (Calculée)', {
            'classes': ('wide',),
            'fields': (
                ('cout_total_global', 'co_financement_global'),
                ('budget_demande_global', 'cout_par_apprenant'),
                ('apprenants_par_session', 'cout_par_session'),
                'pourcentage_a1',
            ),
            'description': "Ces montants sont mis à jour automatiquement via la cascade de calculs.",
        }),
    )
    readonly_fields = (
        'uuid', 'created_by', 'cout_total_global', 'co_financement_global',
        'budget_demande_global', 'cout_par_apprenant', 'apprenants_par_session',
        'cout_par_session', 'pourcentage_a1', 'date_soumission', 'date_approbation',
        'date_demande_modification', 'date_autorisation_modification',
    )
    inlines = [SectionBudgetaireInline]

    def has_add_permission(self, request):
        """Seul l'opérateur peut créer un budget, pas depuis l'admin"""
        return False

    # Action manuelle pour recalculer tout le budget en cas de besoin
    actions = ['forcer_recalcul']

    @admin.action(description="Forcer le recalcul total du budget")
    def forcer_recalcul(self, request, queryset):
        for budget in queryset:
            for section in budget.sections.all():
                for ligne in section.lignes.all():
                    for groupe in ligne.groupes.all():
                        groupe.calculer_groupe() # Déclenche la cascade montante
        self.message_user(request, "Les calculs ont été mis à jour avec succès.")