from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0015_filiere_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='metier',
            name='filiere',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='metiers',
                to='budgets.filiere',
                verbose_name='Filière',
                default=1,
            ),
            preserve_default=False,
        ),
    ]
