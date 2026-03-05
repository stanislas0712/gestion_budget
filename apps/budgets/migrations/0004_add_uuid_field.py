# Generated migration to add UUID field
import uuid
from django.db import migrations, models


def generate_uuids(apps, schema_editor):
    """Generate unique UUIDs for existing records"""
    InfosBudget = apps.get_model('budgets', 'InfosBudget')
    for budget in InfosBudget.objects.all():
        budget.uuid = uuid.uuid4()
        budget.save()


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0003_historicalinfosbudget_created_by_and_more'),
    ]

    operations = [
        # Step 1: Add UUID field without unique constraint
        migrations.AddField(
            model_name='historicalinfosbudget',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='infosbudget',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        # Step 2: Generate UUIDs for existing records
        migrations.RunPython(generate_uuids, reverse_code=migrations.RunPython.noop),
        # Step 3: Make UUID field unique and non-nullable
        migrations.AlterField(
            model_name='historicalinfosbudget',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AlterField(
            model_name='infosbudget',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
