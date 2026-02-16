from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import InfosBudget, SousLigneArticle


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



class InfosBudgetCreationForm(forms.ModelForm):
    """Formulaire simplifie pour la creation d'un budget (3 champs)."""
    class Meta:
        model = InfosBudget
        fields = ['appel_a_projet', 'titre_projet', 'total_apprenants']
        widgets = {
            'appel_a_projet': forms.Select(attrs={'class': 'form-control'}),
            'titre_projet': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'total_apprenants': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        appels_actifs = kwargs.pop('appels_actifs', None)
        super().__init__(*args, **kwargs)
        if appels_actifs is not None:
            self.fields['appel_a_projet'].queryset = appels_actifs
            self.fields['appel_a_projet'].required = True
            self.fields['appel_a_projet'].empty_label = "-- Choisir un appel à projet --"


class InfosBudgetForm(forms.ModelForm):
    """Formulaire simplifie pour la modification d'un budget (memes champs que creation)."""
    class Meta:
        model = InfosBudget
        fields = ['titre_projet', 'total_apprenants']
        widgets = {
            'titre_projet': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'total_apprenants': forms.NumberInput(attrs={'class': 'form-control'}),
        }

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
