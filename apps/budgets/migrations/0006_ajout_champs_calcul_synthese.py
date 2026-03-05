# Generated migration to add new calculated fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0005_renommer_subvention_en_budget_demande'),
    ]

    operations = [
        migrations.AddField(
            model_name='infosbudget',
            name='apprenants_par_session',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='infosbudget',
            name='cout_par_session',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='infosbudget',
            name='pourcentage_a1',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='historicalinfosbudget',
            name='apprenants_par_session',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='historicalinfosbudget',
            name='cout_par_session',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='historicalinfosbudget',
            name='pourcentage_a1',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
