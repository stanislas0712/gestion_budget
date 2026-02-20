from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0012_ajout_cout_total_soumis'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='infosbudget',
            name='cout_total_soumis',
        ),
        migrations.RemoveField(
            model_name='historicalinfosbudget',
            name='cout_total_soumis',
        ),
    ]
