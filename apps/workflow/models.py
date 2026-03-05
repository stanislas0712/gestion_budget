from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from simple_history.models import HistoricalRecords


class WorkflowEvent(models.Model):
    """
    Journal métier (validation, enrichissement, transitions).
    Complète django-auditlog (qui trace les CRUD).
    """

    class Action(models.TextChoices):
        IMPORTED = "imported", "Importé"
        ENRICHED = "enriched", "Enrichi"
        VALIDATED = "validated", "Validé"
        REJECTED = "rejected", "Rejeté"
        SENT_TO_ODOO = "sent_to_odoo", "Envoyé à Odoo"

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    action = models.CharField(max_length=50, choices=Action.choices)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Événement workflow"
        verbose_name_plural = "Événements workflow"
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} ({self.created_at:%Y-%m-%d %H:%M})"

