from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_ajout_actif_manuellement'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='appelaprojet',
            name='actif_manuellement',
        ),
        migrations.RemoveField(
            model_name='historicalappelaprojet',
            name='actif_manuellement',
        ),
    ]
