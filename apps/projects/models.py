from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords

from apps.integrations.goodgrants.models import GoodGrantsApplication
from apps.operators.models import Operator


class AppelAProjet(models.Model):
    nom = models.CharField(max_length=255, verbose_name="Nom de l'appel à projet")
    date_debut = models.DateTimeField(verbose_name="Date de début")
    date_fin = models.DateTimeField(verbose_name="Date de fin")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Appel à projet"
        verbose_name_plural = "Appels à projets"
        ordering = ['-date_debut']

    def __str__(self):
        return self.nom

    @property
    def est_actif(self):
        from django.utils import timezone
        now = timezone.now()
        return self.date_debut <= now <= self.date_fin


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        UNDER_REVIEW = "under_review", "En revue"
        VALIDATED = "validated", "Validé"
        LOCKED = "locked", "Verrouillé"

    gg_application = models.OneToOneField(GoodGrantsApplication, on_delete=models.PROTECT)
    operator = models.ForeignKey(Operator, on_delete=models.PROTECT, related_name="projects")

    title = models.CharField(max_length=255)
    sector = models.CharField(max_length=255, blank=True)
    locations = models.CharField(max_length=255, blank=True)

    approved_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)
    ready_for_convention = models.BooleanField(default=False)

    validated_by_admin = models.BooleanField(default=False)
    admin_comment = models.TextField(blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["ready_for_convention"]),
        ]

    def __str__(self) -> str:
        return self.title

