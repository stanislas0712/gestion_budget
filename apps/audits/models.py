from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords


class IntegrationEvent(models.Model):
    """Traçabilité des échanges inter-systèmes (GoodGrants/Odoo)."""

    class System(models.TextChoices):
        GOODGRANTS = "goodgrants", "GoodGrants"
        ODOO = "odoo", "Odoo"

    class Direction(models.TextChoices):
        INBOUND = "in", "Entrant"
        OUTBOUND = "out", "Sortant"

    class Status(models.TextChoices):
        RECEIVED = "received", "Reçu"
        PROCESSED = "processed", "Traité"
        FAILED = "failed", "Échec"

    system = models.CharField(max_length=50, choices=System.choices)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)

    correlation_id = models.CharField(max_length=100, blank=True)
    external_id = models.CharField(max_length=100, blank=True)

    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Événement intégration"
        verbose_name_plural = "Événements intégrations"
        indexes = [
            models.Index(fields=["system", "direction", "status"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["external_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.system}/{self.direction}/{self.status}"


class AuditLog(models.Model):
    """Logs d'audit des actions utilisateurs."""

    class Action(models.TextChoices):
        CREATE = "create", "Création"
        UPDATE = "update", "Modification"
        DELETE = "delete", "Suppression"
        APPROVE = "approve", "Approbation"
        REJECT = "reject", "Rejet"
        EXPORT = "export", "Export"
        IMPORT = "import", "Import"

    action = models.CharField(max_length=20, choices=Action.choices)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)

    changes = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Log d'audit"
        verbose_name_plural = "Logs d'audit"
        indexes = [
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["user"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} - {self.model_name} #{self.object_id}"