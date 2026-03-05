from __future__ import annotations
import uuid
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from simple_history.models import HistoricalRecords
from django.db.models.signals import post_save
from django.dispatch import receiver

class Filiere(models.Model):
    nom = models.CharField(max_length=255, unique=True, verbose_name="Nom de la filière")
    nombre_max_budgets = models.PositiveIntegerField(default=2, verbose_name="Nombre max de budgets par opérateur")

    class Meta:
        verbose_name = "Filière"
        verbose_name_plural = "Filières"
        ordering = ['nom']

    def __str__(self):
        return self.nom

class Metier(models.Model):
    nom = models.CharField(max_length=255, unique=True, verbose_name="Nom du métier")
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name="metiers", verbose_name="Filière")

    class Meta:
        verbose_name = "Métier"
        verbose_name_plural = "Métiers"
        ordering = ['nom']

    def __str__(self):
        return self.nom

class Localite(models.Model):
    nom = models.CharField(max_length=255, unique=True, verbose_name="Nom de la localité")

    class Meta:
        verbose_name = "Localité"
        verbose_name_plural = "Localités"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class InfosBudget(models.Model):
    """ SYNTHÈSE : En-tête et totaux globaux (A+B) """

    # Statuts possibles
    STATUT_BROUILLON = 'brouillon'
    STATUT_SOUMIS = 'soumis'
    STATUT_DEMANDE_MODIFICATION = 'demande_modification'
    STATUT_MODIFICATION_AUTORISEE = 'modification_autorisee'
    STATUT_APPROUVE = 'approuve'
    STATUT_REJETE = 'rejete'

    STATUTS = [
        (STATUT_BROUILLON, 'Brouillon'),
        (STATUT_SOUMIS, 'Soumis'),
        (STATUT_DEMANDE_MODIFICATION, 'Demande de modification'),
        (STATUT_MODIFICATION_AUTORISEE, 'Modification autorisée'),
        (STATUT_APPROUVE, 'Approuvé'),
        (STATUT_REJETE, 'Rejeté'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Identifiant unique")
    appel_a_projet = models.ForeignKey(
        'projects.AppelAProjet',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="budgets",
        verbose_name="Appel à projet"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Créé par", related_name="budgets_crees")
    operateur = models.CharField(max_length=255, blank=True, default='', verbose_name="Opérateur ou Consortium")
    titre_projet = models.TextField(verbose_name="Titre du projet")
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Filière de formation", related_name="budgets")
    metier = models.ForeignKey(Metier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Métier", related_name="budgets")
    localite = models.ForeignKey(Localite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Localité", related_name="budgets")

    total_apprenants = models.PositiveIntegerField(default=1, verbose_name="Effectif total apprenants")
    nombre_sessions = models.PositiveIntegerField(default=1, verbose_name="Nombre de sessions")

    # Gestion du workflow
    statut = models.CharField(max_length=30, choices=STATUTS, default=STATUT_BROUILLON, verbose_name="Statut")
    motif_demande_modification = models.TextField(blank=True, null=True, verbose_name="Motif de la demande de modification")
    date_soumission = models.DateTimeField(blank=True, null=True, verbose_name="Date de soumission")
    date_demande_modification = models.DateTimeField(blank=True, null=True, verbose_name="Date de demande de modification")
    date_autorisation_modification = models.DateTimeField(blank=True, null=True, verbose_name="Date d'autorisation de modification")
    date_approbation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")

    # Stockage des totaux calculés
    cout_total_global = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    co_financement_global = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_demande_global = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cout_par_apprenant = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Nouveaux champs calculés pour la synthèse
    apprenants_par_session = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cout_par_session = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    pourcentage_a1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    historique = HistoricalRecords()

    def recalculer_tout(self):
        """Force un recalcul complet depuis les articles (bottom-up)"""
        for section in self.sections.all():
            for ligne in section.lignes.all():
                groupes = ligne.groupes.all()
                for groupe in groupes:
                    articles = groupe.articles.all()
                    groupe.cout_total_groupe = sum(a.quantite * a.prix_unitaire for a in articles)
                    groupe.co_financement_groupe = sum(a.co_financement for a in articles)
                    groupe.budget_demande_groupe = groupe.cout_total_groupe - groupe.co_financement_groupe
                    GroupeArticle.objects.filter(pk=groupe.pk).update(
                        cout_total_groupe=groupe.cout_total_groupe,
                        co_financement_groupe=groupe.co_financement_groupe,
                        budget_demande_groupe=groupe.budget_demande_groupe,
                    )
                ligne.cout_total_ligne = sum(g.cout_total_groupe for g in groupes)
                ligne.co_financement_ligne = sum(g.co_financement_groupe for g in groupes)
                ligne.budget_demande_ligne = ligne.cout_total_ligne - ligne.co_financement_ligne
                LigneBudgetaire.objects.filter(pk=ligne.pk).update(
                    cout_total_ligne=ligne.cout_total_ligne,
                    co_financement_ligne=ligne.co_financement_ligne,
                    budget_demande_ligne=ligne.budget_demande_ligne,
                )
            lignes = section.lignes.all()
            section.cout_total_section = sum(l.cout_total_ligne for l in lignes)
            section.co_financement_section = sum(l.co_financement_ligne for l in lignes)
            section.budget_demande_section = section.cout_total_section - section.co_financement_section
            SectionBudgetaire.objects.filter(pk=section.pk).update(
                cout_total_section=section.cout_total_section,
                co_financement_section=section.co_financement_section,
                budget_demande_section=section.budget_demande_section,
            )

    def calculer_synthese(self):
        # Forcer le recalcul complet depuis les articles
        self.recalculer_tout()

        sections = self.sections.all()
        self.cout_total_global = sum(s.cout_total_section for s in sections)
        self.co_financement_global = sum(s.co_financement_section for s in sections)
        self.budget_demande_global = self.cout_total_global - self.co_financement_global

        # Coût unitaire total par apprenant
        if self.total_apprenants > 0:
            self.cout_par_apprenant = self.cout_total_global / Decimal(self.total_apprenants)

        # Nombre d'apprenants par session
        if self.nombre_sessions > 0:
            self.apprenants_par_session = Decimal(self.total_apprenants) / Decimal(self.nombre_sessions)

        # Coût total par session
        if self.nombre_sessions > 0 and self.total_apprenants > 0:
            self.cout_par_session = self.cout_par_apprenant * self.apprenants_par_session

        # Calcul du pourcentage A.1 (basé sur budget demandé uniquement)
        self.pourcentage_a1 = Decimal(0)
        if self.budget_demande_global > 0:
            try:
                ligne_a1 = LigneBudgetaire.objects.get(section__budget_parent=self, code="A.1")
                self.pourcentage_a1 = (ligne_a1.budget_demande_ligne / self.budget_demande_global) * 100
            except LigneBudgetaire.DoesNotExist:
                pass

        # On évite d'appeler save() pour ne pas déclencher les signaux en boucle
        InfosBudget.objects.filter(pk=self.pk).update(
            cout_total_global=self.cout_total_global,
            co_financement_global=self.co_financement_global,
            budget_demande_global=self.budget_demande_global,
            cout_par_apprenant=self.cout_par_apprenant,
            apprenants_par_session=self.apprenants_par_session,
            cout_par_session=self.cout_par_session,
            pourcentage_a1=self.pourcentage_a1
        )

    def verifier_validation_a1(self):
        """Vérifie si A.1 respecte la règle des 30% (sur budget demandé)"""
        if self.budget_demande_global > 0 and self.pourcentage_a1 > 30:
            return False, f"ERREUR : A.1 représente {self.pourcentage_a1:.1f}% du budget demandé (maximum autorisé : 30%)"
        return True, None

    def initialiser_structure(self):
        """Initialise la structure budgétaire si elle n'existe pas"""
        if not self.sections.exists():
            # 1. Création des Sections (A, B)
            sec_a = SectionBudgetaire.objects.create(budget_parent=self, code="A", libelle="Formation")
            sec_b = SectionBudgetaire.objects.create(budget_parent=self, code="B", libelle="Stage + Insertion")

            # 2. Création de Lignes types pour A
            ligne_a1 = LigneBudgetaire.objects.create(section=sec_a, code="A.1", libelle="Matières d'œuvre")
            ligne_a2 = LigneBudgetaire.objects.create(section=sec_a, code="A.2", libelle="Coûts pédagogiques")

            # 3. Création des Groupes pour A.1
            categories_a1 = [
                "Intrants et/ou matières premières",
                "Petites Fournitures Pédagogiques",
            ]

            for nom in categories_a1:
                GroupeArticle.objects.create(
                    libelle=nom,
                    ligne=ligne_a1
                )

            # 4. Création des Groupes pour A.2
            categories_a2 = [
                "Frais pédagogiques",
                "Honoraires",
                "Rapportage",
                "Prise en charge des apprenants",
            ]

            for nom in categories_a2:
                GroupeArticle.objects.create(
                    libelle=nom,
                    ligne=ligne_a2
                )

            # 5. Création d'une seule ligne pour B
            ligne_b = LigneBudgetaire.objects.create(section=sec_b, code="B.1", libelle="Stage et insertion")

            # 6. Création des Groupes pour B (activités d'appui)
            categories_b = [
                "Activités d'appui à l'insertion",
            ]

            for nom in categories_b:
                GroupeArticle.objects.create(
                    libelle=nom,
                    ligne=ligne_b
                )

    def appel_est_actif(self):
        """Vérifie si l'appel à projet lié est encore dans l'intervalle de temps"""
        if not self.appel_a_projet:
            return False
        return self.appel_a_projet.est_actif

    def peut_etre_modifie(self):
        """Vérifie si le budget peut être modifié"""
        # Si l'admin a demandé une modification, l'opérateur peut toujours modifier
        if self.statut == self.STATUT_MODIFICATION_AUTORISEE:
            return True
        # Brouillon ou soumis : modifiable tant que l'appel est actif
        if self.statut in [self.STATUT_BROUILLON, self.STATUT_SOUMIS] and self.appel_est_actif():
            return True
        return False

    def peut_demander_modification(self):
        """Vérifie si une demande de modification peut être faite"""
        return self.statut == self.STATUT_SOUMIS

    def __str__(self) -> str:
        return f"Budget: {self.titre_projet[:50]}"

class SectionBudgetaire(models.Model):
    """ Niveau A, B (FORMATION, ACCOMPAGNEMENT...) """
    budget_parent = models.ForeignKey(InfosBudget, on_delete=models.CASCADE, related_name="sections")
    code = models.CharField(max_length=5) 
    libelle = models.CharField(max_length=255)
    
    cout_total_section = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    co_financement_section = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_demande_section = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        ordering = ['code']

    def calculer_section(self):
        lignes = self.lignes.all()
        self.cout_total_section = sum(l.cout_total_ligne for l in lignes)
        self.co_financement_section = sum(l.co_financement_ligne for l in lignes)
        self.budget_demande_section = self.cout_total_section - self.co_financement_section
        self.save()
        self.budget_parent.calculer_synthese()

class LigneBudgetaire(models.Model):
    """ Niveau A.1, A.2 """
    section = models.ForeignKey(SectionBudgetaire, on_delete=models.CASCADE, related_name="lignes")
    code = models.CharField(max_length=10) 
    libelle = models.CharField(max_length=255)
    
    cout_total_ligne = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    co_financement_ligne = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_demande_ligne = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def clean(self):
        # Validation règle des 30% pour A.1 (basé sur budget demandé)
        if self.code == "A.1" and self.section.budget_parent.budget_demande_global > 0:
            pourcentage = (self.budget_demande_ligne / self.section.budget_parent.budget_demande_global) * 100
            if pourcentage > 30:
                raise ValidationError(f"La ligne A.1 ne peut pas dépasser 30% du budget demandé.")

    def calculer_ligne(self):
        groupes = self.groupes.all()
        self.cout_total_ligne = sum(g.cout_total_groupe for g in groupes)
        self.co_financement_ligne = sum(g.co_financement_groupe for g in groupes)
        self.budget_demande_ligne = self.cout_total_ligne - self.co_financement_ligne
        self.save()
        self.section.calculer_section()

class GroupeArticle(models.Model):
    """ Niveau Middle (Intrants, Honoraires...) """
    ligne = models.ForeignKey(LigneBudgetaire, on_delete=models.CASCADE, related_name="groupes")
    libelle = models.CharField(max_length=255)
    
    cout_total_groupe = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    co_financement_groupe = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_demande_groupe = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def calculer_groupe(self):
        articles = self.articles.all()
        self.cout_total_groupe = sum(a.cout_total_article for a in articles)
        self.co_financement_groupe = sum(a.co_financement for a in articles)
        self.budget_demande_groupe = self.cout_total_groupe - self.co_financement_groupe
        self.save()
        self.ligne.calculer_ligne()

class SousLigneArticle(models.Model):
    """ Saisie réelle par l'utilisateur """
    groupe = models.ForeignKey(GroupeArticle, on_delete=models.CASCADE, related_name="articles")
    designation = models.CharField(max_length=255)
    unite = models.CharField(max_length=50)
    quantite = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prix_unitaire = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    co_financement = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    cout_total_article = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_demande_article = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.cout_total_article = self.quantite * self.prix_unitaire
        self.budget_demande_article = self.cout_total_article - self.co_financement
        super().save(*args, **kwargs)
        self.groupe.calculer_groupe()

# SIGNAL : Initialisation automatique de la structure
@receiver(post_save, sender=InfosBudget)
def initialiser_budget(sender, instance, created, **kwargs):
    if created:
        # 1. Création des Sections (A, B)
        sec_a = SectionBudgetaire.objects.create(budget_parent=instance, code="A", libelle="Formation")
        sec_b = SectionBudgetaire.objects.create(budget_parent=instance, code="B", libelle="Stage + Insertion")

        # 2. Création de Lignes types pour A
        ligne_a1 = LigneBudgetaire.objects.create(section=sec_a, code="A.1", libelle="Matières d'œuvre")
        ligne_a2 = LigneBudgetaire.objects.create(section=sec_a, code="A.2", libelle="Coûts pédagogiques")

        # 3. Création des Groupes pour A.1
        categories_a1 = [
            "Intrants et/ou matières premières",
            "Petites Fournitures Pédagogiques",
        ]

        for nom in categories_a1:
            GroupeArticle.objects.create(
                libelle=nom,
                ligne=ligne_a1
            )

        # 4. Création des Groupes pour A.2
        categories_a2 = [
            "Frais pédagogiques",
            "Honoraires",
            "Rapportage",
            "Prise en charge des apprenants",
        ]

        for nom in categories_a2:
            GroupeArticle.objects.create(
                libelle=nom,
                ligne=ligne_a2
            )

        # 5. Création d'une seule ligne pour B
        ligne_b = LigneBudgetaire.objects.create(section=sec_b, code="B.1", libelle="Stage et insertion")

        # 6. Création des Groupes pour B (activités d'appui)
        categories_b = [
            "Activités d'appui à l'insertion",
        ]

        for nom in categories_b:
            GroupeArticle.objects.create(
                libelle=nom,
                ligne=ligne_b
            )

@receiver(models.signals.post_delete, sender=SousLigneArticle)
def recalculer_apres_suppression(sender, instance, **kwargs):
    """ Force le recalcul du groupe quand un article est supprimé """
    instance.groupe.calculer_groupe()