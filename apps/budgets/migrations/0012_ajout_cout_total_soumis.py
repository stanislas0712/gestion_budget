from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0011_metier_localite_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='infosbudget',
            name='cout_total_soumis',
            field=models.DecimalField(
                blank=True, null=True,
                decimal_places=2, max_digits=15,
                verbose_name='Coût total au moment de la soumission',
                help_text="Montant A+B figé lors de la soumission. Doit rester identique après modification.",
            ),
        ),
        migrations.AddField(
            model_name='historicalinfosbudget',
            name='cout_total_soumis',
            field=models.DecimalField(
                blank=True, null=True,
                decimal_places=2, max_digits=15,
                verbose_name='Coût total au moment de la soumission',
                help_text="Montant A+B figé lors de la soumission. Doit rester identique après modification.",
            ),
        ),
    ]