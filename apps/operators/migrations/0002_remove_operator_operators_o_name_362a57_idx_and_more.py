from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('operators', '0001_initial'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='operator',
            name='operators_o_name_362a57_idx',
        ),
        migrations.RemoveIndex(
            model_name='operator',
            name='operators_o_odoo_id_e5dbce_idx',
        ),
        migrations.RemoveIndex(
            model_name='operator',
            name='operators_o_is_acti_c0f0c5_idx',
        ),
        migrations.RenameField(
            model_name='historicaloperator',
            old_name='odoo_id',
            new_name='odoo_partner_id',
        ),
        migrations.RenameField(
            model_name='operator',
            old_name='odoo_id',
            new_name='odoo_partner_id',
        ),
        migrations.RemoveField(
            model_name='historicaloperator',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='operator',
            name='is_active',
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='acronym',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='contact_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='contact_phone',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='country',
            field=models.CharField(default='Burkina Faso', max_length=100),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='created_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='gg_operator_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='last_synced_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='legal_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='postal_code',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='raw_data',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='status',
            field=models.CharField(choices=[('active', 'Actif'), ('inactive', 'Inactif'), ('suspended', 'Suspendu')], default='active', max_length=20),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='tax_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='type',
            field=models.CharField(choices=[('ngo', 'ONG'), ('association', 'Association'), ('cooperative', 'Coopérative'), ('company', 'Entreprise'), ('other', 'Autre')], default='other', max_length=20),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicaloperator',
            name='website',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='operator',
            name='acronym',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='operator',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='operator',
            name='contact_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='operator',
            name='contact_phone',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='operator',
            name='country',
            field=models.CharField(default='Burkina Faso', max_length=100),
        ),
        migrations.AddField(
            model_name='operator',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='operator',
            name='gg_operator_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='operator',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='operator',
            name='last_synced_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='operator',
            name='legal_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='operator',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='operator',
            name='postal_code',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='operator',
            name='raw_data',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='operator',
            name='status',
            field=models.CharField(choices=[('active', 'Actif'), ('inactive', 'Inactif'), ('suspended', 'Suspendu')], default='active', max_length=20),
        ),
        migrations.AddField(
            model_name='operator',
            name='tax_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='operator',
            name='type',
            field=models.CharField(choices=[('ngo', 'ONG'), ('association', 'Association'), ('cooperative', 'Coopérative'), ('company', 'Entreprise'), ('other', 'Autre')], default='other', max_length=20),
        ),
        migrations.AddField(
            model_name='operator',
            name='verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='operator',
            name='website',
            field=models.URLField(blank=True),
        ),
    ]
