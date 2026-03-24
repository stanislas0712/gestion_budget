from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count
from .models import InfosBudget, SousLigneArticle, Filiere


class InscriptionOperateurForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemple.com'}),
        label="Adresse email"
    )

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Mot de passe'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmer le mot de passe'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un compte avec cette adresse email existe déjà.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Générer le username à partir de l'email (partie avant @)
        email_prefix = self.cleaned_data['email'].split('@')[0]
        base_username = email_prefix
        username = base_username
        counter = 1
        # Gérer les doublons de username
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user



class DisabledOptionSelect(forms.Select):
    """Select widget qui grise certaines options (disabled_choices = dict {id: label_suffix})."""
    def __init__(self, *args, disabled_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.disabled_choices = disabled_choices or {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        str_value = str(value)
        # Chercher dans les clés converties en string
        for k, suffix in self.disabled_choices.items():
            if str(k) == str_value:
                option['attrs']['disabled'] = True
                option['label'] = f"{label} ({suffix})"
                break
        return option


class InfosBudgetCreationForm(forms.ModelForm):
    """Formulaire simplifie pour la creation d'un budget (5 champs)."""
    class Meta:
        model = InfosBudget
        fields = ['appel_a_projet', 'operateur', 'filiere', 'titre_projet', 'total_apprenants']
        widgets = {
            'appel_a_projet': forms.Select(attrs={'class': 'form-control'}),
            'operateur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom de l'opérateur"}),
            'titre_projet': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'total_apprenants': forms.NumberInput(attrs={'class': 'form-control', 'min': '50'}),
        }

    def __init__(self, *args, **kwargs):
        appels_actifs = kwargs.pop('appels_actifs', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if appels_actifs is not None:
            self.fields['appel_a_projet'].queryset = appels_actifs
            self.fields['appel_a_projet'].required = True
            self.fields['appel_a_projet'].empty_label = "-- Choisir un appel à projet --"
        self.fields['filiere'].required = True
        self.fields['filiere'].empty_label = "-- Choisir une filière --"
        self.fields['total_apprenants'].help_text = "Minimum 50 apprenants"

        # Déterminer les filières pleines et utiliser le widget custom
        filieres_pleines = {}
        if self.user:
            budgets_par_filiere = (
                InfosBudget.objects.filter(created_by=self.user, filiere__isnull=False)
                .values('filiere_id', 'filiere__nombre_max_budgets')
                .annotate(nb=Count('id'))
            )
            for entry in budgets_par_filiere:
                max_b = entry['filiere__nombre_max_budgets']
                if entry['nb'] >= max_b:
                    filieres_pleines[entry['filiere_id']] = f"{entry['nb']}/{max_b} budgets"

        self.fields['filiere'].widget = DisabledOptionSelect(
            attrs={'class': 'form-control'},
            disabled_choices=filieres_pleines,
        )
        self.fields['filiere'].widget.choices = self.fields['filiere'].choices

    def clean_total_apprenants(self):
        total = self.cleaned_data.get('total_apprenants')
        if total is not None and total < 50:
            raise forms.ValidationError("Le nombre d'apprenants doit être d'au moins 50.")
        return total

    def clean_filiere(self):
        filiere = self.cleaned_data.get('filiere')
        if filiere and self.user:
            nb = InfosBudget.objects.filter(created_by=self.user, filiere=filiere).count()
            if nb >= filiere.nombre_max_budgets:
                raise forms.ValidationError(
                    f"Vous avez atteint la limite de {filiere.nombre_max_budgets} budgets pour cette filière."
                )
        return filiere


class InfosBudgetForm(forms.ModelForm):
    """Formulaire de modification d'un budget."""
    class Meta:
        model = InfosBudget
        fields = ['titre_projet', 'operateur', 'filiere', 'total_apprenants']
        widgets = {
            'titre_projet': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'operateur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom de l'opérateur"}),
            'filiere': forms.Select(attrs={'class': 'form-select'}),
            'total_apprenants': forms.NumberInput(attrs={'class': 'form-control', 'min': '50'}),
        }

    def clean_total_apprenants(self):
        total = self.cleaned_data.get('total_apprenants')
        if total is not None and total < 50:
            raise forms.ValidationError("Le nombre d'apprenants doit être d'au moins 50.")
        return total

class SousLigneArticleForm(forms.ModelForm):
    class Meta:
        model = SousLigneArticle
        fields = ['designation', 'unite', 'quantite', 'prix_unitaire', 'co_financement']
        widgets = {
            'designation': forms.TextInput(attrs={
                'class': 'form-control form-control-sm', 
                'placeholder': 'Désignation'
            }),
            'unite': forms.TextInput(attrs={
                'class': 'form-control form-control-sm', 
                'placeholder': 'Unité'
            }),
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'hx-post': 'calculer-total-ligne/', # Optionnel: calcul dynamique
                'hx-trigger': 'keyup, change',
                'hx-target': 'closest tr .total-article'
            }),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'co_financement': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }
