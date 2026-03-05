from django.db import migrations, models
import django.db.models.deletion


def migrate_filieres_forward(apps, schema_editor):
    """Crée les Filiere depuis les données existantes et lie les budgets"""
    InfosBudget = apps.get_model('budgets', 'InfosBudget')
    Filiere = apps.get_model('budgets', 'Filiere')

    # Créer les filières uniques depuis les données existantes
    filieres_existantes = InfosBudget.objects.exclude(
        filiere_old__isnull=True
    ).exclude(
        filiere_old=''
    ).values_list('filiere_old', flat=True).distinct()

    filiere_map = {}
    for nom in filieres_existantes:
        obj, _ = Filiere.objects.get_or_create(nom=nom.strip())
        filiere_map[nom.strip()] = obj

    # Lier les budgets aux FK
    for budget in InfosBudget.objects.all():
        if budget.filiere_old and budget.filiere_old.strip() in filiere_map:
            budget.filiere = filiere_map[budget.filiere_old.strip()]
            budget.save()


class Migration(migrations.Migration):

    dependencies = [
        ("budgets", "0014_filiere"),
    ]

    operations = [
        # 1. Mettre à jour le modèle Filiere (unique, verbose_name, max_length, Meta)
        migrations.AlterModelOptions(
            name='filiere',
            options={
                'verbose_name': 'Filière',
                'verbose_name_plural': 'Filières',
                'ordering': ['nom'],
            },
        ),
        migrations.AlterField(
            model_name='filiere',
            name='nom',
            field=models.CharField(max_length=255, unique=True, verbose_name='Nom de la filière'),
        ),

        # 2. Renommer l'ancien champ CharField
        migrations.RenameField(
            model_name='infosbudget',
            old_name='filiere',
            new_name='filiere_old',
        ),
        migrations.RenameField(
            model_name='historicalinfosbudget',
            old_name='filiere',
            new_name='filiere_old',
        ),

        # 3. Ajouter la nouvelle FK (nullable)
        migrations.AddField(
            model_name='infosbudget',
            name='filiere',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='budgets',
                to='budgets.filiere',
                verbose_name='Filière de formation',
            ),
        ),
        migrations.AddField(
            model_name='historicalinfosbudget',
            name='filiere',
            field=models.ForeignKey(
                blank=True, null=True,
                db_constraint=False,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+',
                to='budgets.filiere',
                verbose_name='Filière de formation',
            ),
        ),

        # 4. Migrer les données
        migrations.RunPython(migrate_filieres_forward, migrations.RunPython.noop),

        # 5. Supprimer les anciens champs CharField
        migrations.RemoveField(
            model_name='infosbudget',
            name='filiere_old',
        ),
        migrations.RemoveField(
            model_name='historicalinfosbudget',
            name='filiere_old',
        ),
    ]
