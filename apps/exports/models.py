from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords


class ExportJob(models.Model):
    """
    Trace des exports (Excel/PDF) à des fins d'audit et de reproductibilité.
    """

    class Kind(models.TextChoices):
        CONVENTION_XLSX = "convention_xlsx", "Convention (Excel)"
        BUDGET_PDF = "budget_pdf", "Budget (PDF)"

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        RUNNING = "running", "En cours"
        DONE = "done", "Terminé"
        FAILED = "failed", "Échec"

    kind = models.CharField(max_length=50, choices=Kind.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    parameters = models.JSONField(default=dict, blank=True)
    result_file = models.FileField(upload_to="exports/", null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Job export"
        verbose_name_plural = "Jobs exports"
        indexes = [
            models.Index(fields=["kind", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind} ({self.status})"

