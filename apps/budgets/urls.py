from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    path('', views.budget_dashboard, name='dashboard'),
    path('creer/', views.creer_budget, name='creer_budget'),
    path('<uuid:uuid>/', views.budget_detail, name='budget_detail'),
    path('<uuid:uuid>/modifier/', views.modifier_budget, name='modifier_budget'),
    path('<uuid:uuid>/supprimer/', views.supprimer_budget, name='supprimer_budget'),

    # HTMX
    path('ajouter-ligne/<int:groupe_id>/', views.afficher_formulaire_ligne, name='ajouter_ligne'),
    path('sauvegarder-ligne/<int:groupe_id>/', views.sauvegarder_ligne, name='sauvegarder_ligne'),
    path('supprimer-article/<int:article_id>/', views.supprimer_article, name='supprimer_article'),
    path('get-synthese/<uuid:uuid>/', views.get_synthese, name='get_synthese'),
    path('get-statut/<uuid:uuid>/', views.get_budget_statut, name='get_budget_statut'),
    path('get-appel-statut/', views.get_appel_statut, name='get_appel_statut'),
    path('get-pourcentage-a1/<uuid:uuid>/', views.get_pourcentage_a1, name='get_pourcentage_a1'),
    path('get-total-section/<int:section_id>/', views.get_total_section, name='get_total_section'),

    # Exports
    path('export-excel/<uuid:uuid>/', views.export_excel, name='export_excel'),
    path('export-pdf/<uuid:uuid>/', views.export_pdf, name='export_pdf'),
    path('export-word/<uuid:uuid>/', views.export_word, name='export_word'),

    # Téléchargement templates vierges
    path('telecharger-template/<str:format>/', views.telecharger_template, name='telecharger_template'),

    # Profil
    path('profil/', views.profil, name='profil'),
    path('profil/changer-mot-de-passe/', views.changer_mot_de_passe, name='changer_mot_de_passe'),

    # Prévisualisation emails (admin uniquement)
    path('preview-email/modification/', views.preview_email_modification, name='preview_email_modification'),

    # Workflow de validation
    path('<uuid:uuid>/soumettre/', views.soumettre_budget, name='soumettre_budget'),
    path('<uuid:uuid>/demander-modification/', views.demander_modification, name='demander_modification'),
    path('<uuid:uuid>/approuver/', views.approuver_budget, name='approuver_budget'),
    path('<uuid:uuid>/rejeter/', views.rejeter_budget, name='rejeter_budget'),
]