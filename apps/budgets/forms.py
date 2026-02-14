from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import InfosBudget, SousLigneArticle


class InscriptionOperateurForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
        label="Prénom"
    )
    last_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
        label="Nom"
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemple.com'}),
        label="Adresse email"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Mot de passe'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmer le mot de passe'})



class InfosBudgetForm(forms.ModelForm):
    class Meta:
        model = InfosBudget
        fields = [
            'appel_a_projet', 'operateur', 'titre_projet', 'filiere',
            'metier', 'localite', 'total_apprenants',
            'nombre_sessions'
        ]
        widgets = {
            'appel_a_projet': forms.Select(attrs={'class': 'form-control'}),
            'titre_projet': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'operateur': forms.TextInput(attrs={'class': 'form-control'}),
            'filiere': forms.Select(attrs={'class': 'form-control'}),
            'metier': forms.Select(attrs={'class': 'form-control'}),
            'localite': forms.Select(attrs={'class': 'form-control'}),
            'total_apprenants': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_sessions': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        appels_actifs = kwargs.pop('appels_actifs', None)
        super().__init__(*args, **kwargs)
        if appels_actifs is not None:
            self.fields['appel_a_projet'].queryset = appels_actifs
            self.fields['appel_a_projet'].required = True
            self.fields['appel_a_projet'].empty_label = "-- Choisir un appel à projet --"
        else:
            # En mode modification, cacher le champ appel_a_projet
            self.fields.pop('appel_a_projet', None)

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
