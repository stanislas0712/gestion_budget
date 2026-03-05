from django.db import models
from simple_history.models import HistoricalRecords

from apps.projects.models import Project


class Convention(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        VALIDATED = "validated", "Validée"
        SENT_TO_ODOO = "sent_to_odoo", "Envoyée à Odoo"

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="convention")

    reference = models.CharField(max_length=100, unique=True)
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
    def is_editable(self) -> bool:
        return self.status == self.Status.DRAFT

    def __str__(self) -> str:
        return self.reference

