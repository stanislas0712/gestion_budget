from rest_framework import serializers
from decimal import Decimal
from .models import (
    InfosBudget, SectionBudgetaire, LigneBudgetaire,
    GroupeArticle, SousLigneArticle
)

class SousLigneArticleSerializer(serializers.ModelSerializer):
    # On utilise les champs calculés en base de données (plus rapide)
    class Meta:
        model = SousLigneArticle
        fields = [
            'id', 'designation', 'unite', 'quantite', 'prix_unitaire', 
            'co_financement', 'cout_total_article', 'budget_demande_article'
        ]
        read_only_fields = ['cout_total_article', 'budget_demande_article']

    def validate(self, data):
        # Validation du cofinancement au niveau de l'article
        quantite = data.get('quantite', 0)
        prix = data.get('prix_unitaire', 0)
        co_financement = data.get('co_financement', 0)
        
        if co_financement > (quantite * prix):
            raise serializers.ValidationError(
                {"co_financement": "Le cofinancement ne peut pas dépasser le coût total de l'article."}
            )
        return data

class GroupeArticleSerializer(serializers.ModelSerializer):
    articles = SousLigneArticleSerializer(many=True, read_only=True)

    class Meta:
        model = GroupeArticle
        fields = ['id', 'libelle', 'cout_total_groupe', 'co_financement_groupe', 'budget_demande_groupe', 'articles']
        read_only_fields = ['cout_total_groupe', 'co_financement_groupe', 'budget_demande_groupe']

class LigneBudgetaireSerializer(serializers.ModelSerializer):
    groupes = GroupeArticleSerializer(many=True, read_only=True)

    class Meta:
        model = LigneBudgetaire
        fields = ['id', 'code', 'libelle', 'cout_total_ligne', 'budget_demande_ligne', 'groupes']

class SectionBudgetaireSerializer(serializers.ModelSerializer):
    lignes = LigneBudgetaireSerializer(many=True, read_only=True)

    class Meta:
        model = SectionBudgetaire
        fields = ['id', 'code', 'libelle', 'cout_total_section', 'co_financement_section', 'budget_demande_section', 'lignes']
        read_only_fields = ['cout_total_section', 'co_financement_section', 'budget_demande_section']

class InfosBudgetSerializer(serializers.ModelSerializer):
    # On imbrique les sections pour avoir la vue complète
    sections = serializers.SerializerMethodField()

    class Meta:
        model = InfosBudget
        fields = [
            'id', 'operateur', 'titre_projet', 'filiere', 'total_apprenants',
            'cout_total_global', 'co_financement_global', 'budget_demande_global',
            'cout_par_apprenant', 'sections'
        ]
        read_only_fields = ['cout_total_global', 'co_financement_global', 'budget_demande_global', 'cout_par_apprenant']

    def get_sections(self, obj):
        # On trie par code (A, B)
        sections = obj.sections.all().order_by('code')
        # On pourrait créer un SectionBudgetaireSerializer si besoin de plus de détails
        return SectionBudgetaireSerializer(sections, many=True).data

    def validate(self, data):
        """
        Règle métier des 30% :
        On vérifie si la ligne A.1 (Matière d'œuvre) ne dépasse pas 30% du budget demandé.
        """
        instance = self.instance
        if instance and instance.budget_demande_global > 0:
            # On cherche la ligne A.1 dans ce budget
            ligne_a1 = LigneBudgetaire.objects.filter(section__budget_parent=instance, code="A.1").first()
            if ligne_a1:
                pourcentage = (ligne_a1.budget_demande_ligne / instance.budget_demande_global) * 100
                if pourcentage > 30:
                    raise serializers.ValidationError(
                        "Alerte : La ligne A.1 (Matière d'œuvre) dépasse 30% du budget demandé."
                    )
        return data