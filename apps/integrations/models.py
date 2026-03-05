"""
Models at the integrations boundary.

Important: business logic should live in services, not in these archive/log models.
"""

from django.db import models


class IntegrationHealth(models.Model):
    """
    Very small table to keep a heartbeat / last successful sync per system.
    """

    system = models.CharField(max_length=50, unique=True)  # e.g. "goodgrants", "odoo"
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error_at = models.DateTimeField(null=True, blank=True)
    last_error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Santé intégration"
        verbose_name_plural = "Santé intégrations"

    def __str__(self) -> str:
        return self.system

