from django.db import migrations, models
import django.db.models.deletion


def migrate_data_forward(apps, schema_editor):
    """Crée les Metier/Localite depuis les données existantes et lie les budgets"""
    InfosBudget = apps.get_model('budgets', 'InfosBudget')
    Metier = apps.get_model('budgets', 'Metier')
    Localite = apps.get_model('budgets', 'Localite')

    # Créer les métiers uniques depuis les données existantes
    metiers_existants = InfosBudget.objects.exclude(
        metiers_old__isnull=True
    ).exclude(
        metiers_old=''
    ).values_list('metiers_old', flat=True).distinct()

    metier_map = {}
    for nom in metiers_existants:
        obj, _ = Metier.objects.get_or_create(nom=nom.strip())
        metier_map[nom.strip()] = obj

    # Créer les localités uniques depuis les données existantes
    localites_existantes = InfosBudget.objects.exclude(
        localite_old__isnull=True
    ).exclude(
        localite_old=''
    ).values_list('localite_old', flat=True).distinct()

    localite_map = {}
    for nom in localites_existantes:
        obj, _ = Localite.objects.get_or_create(nom=nom.strip())
        localite_map[nom.strip()] = obj

    # Lier les budgets aux FK
    for budget in InfosBudget.objects.all():
        if budget.metiers_old and budget.metiers_old.strip() in metier_map:
            budget.metier = metier_map[budget.metiers_old.strip()]
        if budget.localite_old and budget.localite_old.strip() in localite_map:
            budget.localite = localite_map[budget.localite_old.strip()]
        budget.save()


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0010_historicalinfosbudget_appel_a_projet_and_more'),
    ]

    operations = [
        # 1. Créer les modèles Metier et Localite
        migrations.CreateModel(
            name='Metier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, unique=True, verbose_name='Nom du métier')),
            ],
            options={
                'verbose_name': 'Métier',
                'verbose_name_plural': 'Métiers',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Localite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, unique=True, verbose_name='Nom de la localité')),
            ],
            options={
                'verbose_name': 'Localité',
                'verbose_name_plural': 'Localités',
                'ordering': ['nom'],
            },
        ),

        # 2. Renommer les anciens champs CharField
        migrations.RenameField(
            model_name='infosbudget',
            old_name='metiers',
            new_name='metiers_old',
        ),
        migrations.RenameField(
            model_name='infosbudget',
            old_name='localite',
            new_name='localite_old',
        ),
        migrations.RenameField(
            model_name='historicalinfosbudget',
            old_name='metiers',
            new_name='metiers_old',
        ),
        migrations.RenameField(
            model_name='historicalinfosbudget',
            old_name='localite',
            new_name='localite_old',
        ),

        # 3. Ajouter les nouvelles FK (nullable)
        migrations.AddField(
            model_name='infosbudget',
            name='metier',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='budgets',
                to='budgets.metier',
                verbose_name='Métier',
            ),
        ),
        migrations.AddField(
            model_name='infosbudget',
            name='localite',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='budgets',
                to='budgets.localite',
                verbose_name='Localité',
            ),
        ),
        migrations.AddField(
            model_name='historicalinfosbudget',
            name='metier',
            field=models.ForeignKey(
                blank=True, null=True,
                db_constraint=False,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+',
                to='budgets.metier',
                verbose_name='Métier',
            ),
        ),
        migrations.AddField(
            model_name='historicalinfosbudget',
            name='localite',
            field=models.ForeignKey(
                blank=True, null=True,
                db_constraint=False,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+',
                to='budgets.localite',
                verbose_name='Localité',
            ),
        ),

        # 4. Migrer les données
        migrations.RunPython(migrate_data_forward, migrations.RunPython.noop),

        # 5. Supprimer les anciens champs CharField
        migrations.RemoveField(
            model_name='infosbudget',
            name='metiers_old',
        ),
        migrations.RemoveField(
            model_name='infosbudget',
            name='localite_old',
        ),
        migrations.RemoveField(
            model_name='historicalinfosbudget',
            name='metiers_old',
        ),
        migrations.RemoveField(
            model_name='historicalinfosbudget',
            name='localite_old',
        ),
    ]
