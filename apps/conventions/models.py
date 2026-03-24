from django.db import models
from simple_history.models import HistoricalRecords

from apps.projects.models import Project


class Convention(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        VALIDATED = "validated", "Validée"
        SENT_TO_ODOO = "sent_to_odoo", "Envoyée à Odoo"

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="convention")
<<<<<<< HEAD
    budget = models.OneToOneField(
        'budgets.InfosBudget',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="convention",
        verbose_name="Budget"
    )

    reference = models.CharField(max_length=100, unique=True, verbose_name="Numéro de la convention")
    date_signature = models.DateField(null=True, blank=True, verbose_name="Date de signature")
    dure_convention = models.PositiveIntegerField(null=True, blank=True, verbose_name="Durée de la convention (en mois)") 
=======

    reference = models.CharField(max_length=100, unique=True)
>>>>>>> 052578e1e8b11c61f5334ebd3f068aefcfadd3b2
    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)
    validated_at = models.DateTimeField(null=True, blank=True)

    odoo_id = models.IntegerField(null=True, blank=True)
    sent_to_odoo_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Convention"
        verbose_name_plural = "Conventions"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["reference"]),
            models.Index(fields=["odoo_id"]),
        ]

    @property
<<<<<<< HEAD
    def montant(self):
        """Montant de la convention (budget demandé global du budget lié)"""
        if self.budget:
            return self.budget.budget_demande_global
        return None

    @property
    def cofinancement(self):
        """Cofinancement global du budget lié"""
        if self.budget:
            return self.budget.co_financement_global
        return None

    @property
=======
>>>>>>> 052578e1e8b11c61f5334ebd3f068aefcfadd3b2
    def is_editable(self) -> bool:
        return self.status == self.Status.DRAFT

    def __str__(self) -> str:
        return self.reference

