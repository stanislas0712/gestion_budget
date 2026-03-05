from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords

class Operator(models.Model):
    class Type(models.TextChoices):
        NGO = 'ngo', 'ONG'
        ASSOCIATION = 'association', 'Association'
        COOPERATIVE = 'cooperative', 'Coopérative'
        COMPANY = 'company', 'Entreprise'
        OTHER = 'other', 'Autre'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Actif'
        INACTIVE = 'inactive', 'Inactif'
        SUSPENDED = 'suspended', 'Suspendu'

    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    acronym = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.OTHER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="Burkina Faso")
    address = models.TextField(blank=True)

    registration_number = models.CharField(max_length=100, blank=True)
    gg_operator_id = models.CharField(max_length=100, null=True, blank=True) 
    odoo_partner_id = models.IntegerField(null=True, blank=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Opérateur"
        verbose_name_plural = "Opérateurs"

    def verify(self):
        from django.utils import timezone
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save()

    def __str__(self) -> str:
        return self.name