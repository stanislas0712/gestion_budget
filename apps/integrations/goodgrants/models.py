from django.db import models
from simple_history.models import HistoricalRecords


class GoodGrantsApplication(models.Model):
    """
    Archive immuable de la demande validée (preuve/audit).
    Aucune logique métier ici.
    """

    gg_id = models.CharField(max_length=100, unique=True)
    raw_payload = models.JSONField()

    status = models.CharField(max_length=50)
    validated_at = models.DateTimeField(null=True, blank=True)

    synced = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)

    received_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Demande GoodGrants"
        verbose_name_plural = "Demandes GoodGrants"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["validated_at"]),
            models.Index(fields=["synced"]),
        ]

    def __str__(self) -> str:
        return f"GG {self.gg_id}"

