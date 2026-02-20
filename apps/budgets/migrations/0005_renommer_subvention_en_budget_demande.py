# Generated migration to rename subvention fields to budget_demande

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0004_add_uuid_field'),
    ]

    operations = [
        # InfosBudget
        migrations.RenameField(
            model_name='infosbudget',
            old_name='subvention_demandee_globale',
            new_name='budget_demande_global',
        ),
        migrations.RenameField(
            model_name='historicalinfosbudget',
            old_name='subvention_demandee_globale',
            new_name='budget_demande_global',
        ),

        # SectionBudgetaire
        migrations.RenameField(
            model_name='sectionbudgetaire',
            old_name='subvention_section',
            new_name='budget_demande_section',
        ),

        # LigneBudgetaire
        migrations.RenameField(
            model_name='lignebudgetaire',
            old_name='subvention_ligne',
            new_name='budget_demande_ligne',
        ),

        # GroupeArticle
        migrations.RenameField(
            model_name='groupearticle',
            old_name='subvention_groupe',
            new_name='budget_demande_groupe',
        ),
    ]
