from rest_framework import serializers

from .models import Convention


class ConventionSerializer(serializers.ModelSerializer):
    montant = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    cofinancement = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Convention
        fields = [
            'id',
            'reference',
            'date_signature',
            'start_date',
            'end_date',
            'project',
            'budget',
            'montant',
            'cofinancement',
            'status',
            'validated_at',
            'odoo_id',
            'sent_to_odoo_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['montant', 'cofinancement', 'validated_at', 'sent_to_odoo_at', 'created_at', 'updated_at']
