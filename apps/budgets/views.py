import threading
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, login
from django.contrib import messages
from django.contrib.auth.models import User
from .models import InfosBudget, GroupeArticle, SousLigneArticle, SectionBudgetaire
from .forms import SousLigneArticleForm, InfosBudgetForm, InscriptionOperateurForm


def _envoyer_email_async(subject, message, recipient_list):
    """Envoie un email dans un thread séparé pour ne pas bloquer la requête."""
    from django.core.mail import send_mail
    from django.conf import settings

    def _send():
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erreur envoi email: {e}")

    threading.Thread(target=_send, daemon=True).start()

def inscription(request):
    """Inscription d'un nouvel opérateur (utilisateur sans droits admin)"""
    if request.user.is_authenticated:
        return redirect('budgets:dashboard')

    if request.method == 'POST':
        form = InscriptionOperateurForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            login(request, user)
            messages.success(request, f"Bienvenue {user.get_full_name()} ! Votre compte opérateur a été créé avec succès.")
            return redirect('budgets:dashboard')
    else:
        form = InscriptionOperateurForm()

    return render(request, 'registration/inscription.html', {'form': form})


@login_required
def budget_detail(request, uuid):
    budget = get_object_or_404(InfosBudget, uuid=uuid)

    # Un opérateur ne peut voir que ses propres budgets
    if not (request.user.is_staff or request.user.is_superuser):
        if budget.created_by != request.user:
            messages.error(request, "Vous n'avez pas accès à ce budget.")
            return redirect('budgets:dashboard')

    # S'assurer que la structure budgétaire est initialisée
    budget.initialiser_structure()
    # Forcer le rafraîchissement des données depuis la base
    budget.refresh_from_db()

    context = {'budget': budget}

    # Formulaire de modification pour l'opérateur (modal)
    if budget.peut_etre_modifie() and not request.user.is_staff and not request.user.is_superuser:
        context['modifier_form'] = InfosBudgetForm(instance=budget)

    return render(request, 'budgets/budget.html', context)

@login_required
def afficher_formulaire_ligne(request, groupe_id):
    """ Renvoie la ligne de formulaire <tr> """
    groupe = get_object_or_404(GroupeArticle, pk=groupe_id)
    return render(request, 'budgets/subline_form.html', {
        'groupe': groupe
    })

@login_required
def sauvegarder_ligne(request, groupe_id):
    """ Sauvegarde et demande le rafraîchissement des totaux """
    groupe = get_object_or_404(GroupeArticle, pk=groupe_id)

    # Vérifier que le budget est modifiable (statut + appel actif)
    budget = groupe.ligne.section.budget_parent
    if not budget.peut_etre_modifie():
        return HttpResponse("Ce budget ne peut pas être modifié.", status=403)

    # L'admin ne peut pas ajouter de lignes
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponse("Les administrateurs ne peuvent pas modifier les budgets.", status=403)

    if request.method == "POST":
        try:
            article = SousLigneArticle.objects.create(
                groupe=groupe,
                designation=request.POST.get('designation', ''),
                unite=request.POST.get('unite', ''),
                quantite=float(request.POST.get('quantite', 1)),
                prix_unitaire=float(request.POST.get('prix_unitaire', 0)),
                co_financement=float(request.POST.get('co_financement', 0))
            )

            response = render(request, 'partials/subline_row.html', {'article': article, 'budget': budget})
            response['HX-Trigger'] = 'refreshTotals'
            return response
        except (ValueError, TypeError) as e:
            return HttpResponse(f"Erreur de données: {str(e)}", status=400)

    return HttpResponse("Méthode non autorisée", status=405)

@login_required
def supprimer_article(request, article_id):
    """Supprime un article via HTMX"""
    article = get_object_or_404(SousLigneArticle, pk=article_id)

    # Vérifier que le budget est modifiable
    budget = article.groupe.ligne.section.budget_parent
    if not budget.peut_etre_modifie():
        return HttpResponse("Ce budget ne peut pas être modifié.", status=403)

    if request.user.is_staff or request.user.is_superuser:
        return HttpResponse("Les administrateurs ne peuvent pas modifier les budgets.", status=403)

    article.delete()
    
    # Retourne une réponse vide avec le trigger pour rafraîchir les totaux
    response = HttpResponse("")
    response['HX-Trigger'] = 'refreshTotals'
    return response

@login_required
def get_synthese(request, uuid):
    budget = get_object_or_404(InfosBudget, uuid=uuid)
    budget.calculer_synthese()
    return render(request, 'budgets/synthese_header.html', {'budget': budget})

@login_required
def get_budget_statut(request, uuid):
    """Retourne le statut actuel du budget en JSON (pour le polling temps réel)"""
    budget = get_object_or_404(InfosBudget, uuid=uuid)
    return JsonResponse({
        'statut': budget.statut,
        'statut_display': budget.get_statut_display(),
        'motif': budget.motif_demande_modification or '',
    })

@login_required
def get_pourcentage_a1(request, uuid):
    """Retourne le pourcentage A1 et les infos de validation en JSON"""
    budget = get_object_or_404(InfosBudget, uuid=uuid)
    budget.calculer_synthese()
    budget.refresh_from_db()

    return JsonResponse({
        'pourcentage_a1': float(budget.pourcentage_a1),
        'cout_total_global': float(budget.cout_total_global),
        'depasse_30': float(budget.pourcentage_a1) > 30,
    })

@login_required
def get_appel_statut(request):
    """Retourne le nombre d'appels actifs (pour le polling temps réel)"""
    from apps.projects.models import AppelAProjet
    from django.utils import timezone as tz
    now = tz.now()
    count = AppelAProjet.objects.filter(
        date_debut__lte=now, date_fin__gte=now
    ).count()
    return JsonResponse({
        'count': count,
    })

@login_required
def budget_dashboard(request):
    from apps.projects.models import AppelAProjet
    from .models import Filiere, Localite
    from django.utils import timezone as tz
    from django.core.paginator import Paginator

    query = request.GET.get('q')
    filtre_appel = request.GET.get('appel')
    filtre_filiere = request.GET.get('filiere')
    filtre_localite = request.GET.get('localite')

    is_admin = request.user.is_staff or request.user.is_superuser
    has_filters = query or filtre_appel or filtre_filiere or filtre_localite

    if is_admin:
        budgets = InfosBudget.objects.all()
    else:
        if has_filters:
            budgets = InfosBudget.objects.filter(created_by=request.user)
        else:
            budgets = InfosBudget.objects.none()

    if query:
        budgets = budgets.filter(
            Q(titre_projet__icontains=query) |
            Q(operateur__icontains=query) |
            Q(filiere__nom__icontains=query) |
            Q(localite__nom__icontains=query) |
            Q(metier__nom__icontains=query)
        )
    if filtre_appel:
        budgets = budgets.filter(appel_a_projet_id=filtre_appel)
    if filtre_filiere:
        budgets = budgets.filter(filiere_id=filtre_filiere)
    if filtre_localite:
        budgets = budgets.filter(localite_id=filtre_localite)

    budgets = budgets.order_by('-id')

    # Pagination : 10 budgets par page
    paginator = Paginator(budgets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Récupérer tous les appels à projet actifs
    now = tz.now()
    appels_actifs = AppelAProjet.objects.filter(
        date_debut__lte=now, date_fin__gte=now
    )

    # Listes pour les filtres
    tous_appels = AppelAProjet.objects.all().order_by('-date_debut')
    toutes_filieres = Filiere.objects.all()
    toutes_localites = Localite.objects.all()

    # Formulaire de création dans le modal (opérateurs uniquement)
    budget_form = None
    if not is_admin and appels_actifs.exists():
        budget_form = InfosBudgetForm(appels_actifs=appels_actifs)

    return render(request, 'budgets/dashboard.html', {
        'budgets': page_obj,
        'page_obj': page_obj,
        'query': query,
        'is_admin': is_admin,
        'appels_actifs': appels_actifs,
        'tous_appels': tous_appels,
        'toutes_filieres': toutes_filieres,
        'toutes_localites': toutes_localites,
        'filtre_appel': filtre_appel,
        'filtre_filiere': filtre_filiere,
        'filtre_localite': filtre_localite,
        'budget_form': budget_form,
    })

@login_required
def creer_budget(request):
    from apps.projects.models import AppelAProjet
    from django.utils import timezone

    # L'admin ne peut pas créer de budget
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, "Les administrateurs ne sont pas autorisés à créer des budgets.")
        return redirect('budgets:dashboard')

    # Récupérer tous les appels à projet actifs
    now = timezone.now()
    appels_actifs = AppelAProjet.objects.filter(
        date_debut__lte=now, date_fin__gte=now
    )
    if not appels_actifs.exists():
        messages.error(request, "Aucun appel à projet n'est actif actuellement. Vous ne pouvez pas créer de budget en dehors de la période d'appel.")
        return redirect('budgets:dashboard')

    if request.method == "POST":
        form = InfosBudgetForm(request.POST, appels_actifs=appels_actifs)
        if form.is_valid():
            nouveau_budget = form.save(commit=False)
            nouveau_budget.created_by = request.user
            nouveau_budget.save()
            return redirect('budgets:budget_detail', uuid=nouveau_budget.uuid)
        else:
            # Erreur de validation : afficher le dashboard avec le modal ouvert
            from .models import Filiere, Localite
            from django.utils import timezone as tz
            from django.core.paginator import Paginator

            now = tz.now()
            budgets = InfosBudget.objects.none()
            paginator = Paginator(budgets, 10)
            page_obj = paginator.get_page(1)
            tous_appels = AppelAProjet.objects.all().order_by('-date_debut')

            return render(request, 'budgets/dashboard.html', {
                'budgets': page_obj,
                'page_obj': page_obj,
                'query': None,
                'is_admin': False,
                'appels_actifs': appels_actifs,
                'tous_appels': tous_appels,
                'toutes_filieres': Filiere.objects.all(),
                'toutes_localites': Localite.objects.all(),
                'filtre_appel': None,
                'filtre_filiere': None,
                'filtre_localite': None,
                'budget_form': form,
                'show_modal': True,
            })

    return redirect('budgets:dashboard')

@login_required
def modifier_budget(request, uuid):
    """Modifie les infos d'un budget - interdit aux admins"""
    # L'admin ne peut pas modifier les budgets
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, "Les administrateurs ne sont pas autorisés à modifier les budgets.")
        return redirect('budgets:budget_detail', uuid=uuid)

    budget = get_object_or_404(InfosBudget, uuid=uuid)

    # Vérifier que l'opérateur est le créateur
    if budget.created_by != request.user:
        messages.error(request, "Vous n'avez pas accès à ce budget.")
        return redirect('budgets:dashboard')

    # Vérifier que le budget est modifiable (statut + appel actif)
    if not budget.peut_etre_modifie():
        messages.error(request, "Ce budget ne peut pas être modifié dans son état actuel.")
        return redirect('budgets:budget_detail', uuid=uuid)

    if request.method == "POST":
        form = InfosBudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, "Budget modifié avec succès.")
            return redirect('budgets:budget_detail', uuid=budget.uuid)
        else:
            # Erreur : réafficher la page budget avec le modal ouvert
            budget.initialiser_structure()
            budget.refresh_from_db()
            return render(request, 'budgets/budget.html', {
                'budget': budget,
                'modifier_form': form,
                'show_modifier_modal': True,
            })

    return redirect('budgets:budget_detail', uuid=budget.uuid)

@login_required
def supprimer_budget(request, uuid):
    """Suppression désactivée sur la plateforme. Utiliser l'admin Django."""
    messages.error(request, "La suppression de budgets n'est pas autorisée depuis la plateforme. Contactez l'administrateur Django.")
    return redirect('budgets:dashboard')

@login_required
def get_total_section(request, section_id):
    section = get_object_or_404(SectionBudgetaire, id=section_id)
    return render(request, 'budgets/partials/section_total.html', {
        'section': section
    })

# ========================= EXPORTS =========================

@login_required
def export_excel(request, uuid):
    """Exporte un budget en format Excel (réservé aux admins)"""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponse("Accès non autorisé", status=403)

    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from decimal import Decimal

    budget = get_object_or_404(InfosBudget, uuid=uuid)
    budget.calculer_synthese()

    wb = Workbook()
    ws = wb.active
    ws.title = "Budget"

    # Styles
    header_fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
    section_fill = PatternFill(start_color="343a40", end_color="343a40", fill_type="solid")
    ligne_fill = PatternFill(start_color="6c757d", end_color="6c757d", fill_type="solid")
    groupe_fill = PatternFill(start_color="d1ecf1", end_color="d1ecf1", fill_type="solid")
    subtotal_fill = PatternFill(start_color="fff3cd", end_color="fff3cd", fill_type="solid")
    green_fill = PatternFill(start_color="d4edda", end_color="d4edda", fill_type="solid")
    synthese_title_fill = PatternFill(start_color="b8daff", end_color="b8daff", fill_type="solid")
    synthese_info_fill = PatternFill(start_color="d1ecf1", end_color="d1ecf1", fill_type="solid")
    synthese_warn_fill = PatternFill(start_color="fff3cd", end_color="fff3cd", fill_type="solid")
    synthese_success_fill = PatternFill(start_color="c3e6cb", end_color="c3e6cb", fill_type="solid")

    header_font = Font(bold=True, color="FFFFFF", size=10)
    section_font = Font(bold=True, color="FFFFFF", size=10)
    ligne_font = Font(bold=True, color="FFFFFF", size=10)
    groupe_font = Font(bold=True, size=9)
    bold_font = Font(bold=True, size=9)

    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    center = Alignment(horizontal='center', vertical='center')
    right = Alignment(horizontal='right', vertical='center')
    left = Alignment(horizontal='left', vertical='center')

    def style_row(row, cols, font=None, fill=None, alignment=None, number_format=None):
        for col in cols:
            c = ws[f'{col}{row}']
            c.border = thin_border
            if font: c.font = font
            if fill: c.fill = fill
            if alignment: c.alignment = alignment
            if number_format: c.number_format = number_format

    # Titre
    ws.merge_cells('A1:H1')
    ws['A1'].value = f"BUDGET - {budget.titre_projet}"
    ws['A1'].font = Font(bold=True, size=14, color="667eea")
    ws['A1'].alignment = center

    # Infos générales
    row = 3
    info_labels = [
        ("Opérateur:", str(budget.operateur)),
        ("Filière:", str(budget.filiere) if budget.filiere else ""),
        ("Apprenants:", str(budget.total_apprenants) + "     |     Sessions: " + str(budget.nombre_sessions)),
    ]
    for label, value in info_labels:
        ws[f'A{row}'] = label
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'A{row}'].border = thin_border
        ws.merge_cells(f'B{row}:H{row}')
        ws[f'B{row}'] = value
        ws[f'B{row}'].border = thin_border
        row += 1

    # En-têtes colonnes
    row += 1
    headers = ["Code", "Désignation", "Unité", "Qté", "Prix Unit.", "Coût Total", "Co-financement", "Budget demandé"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = thin_border
    row += 1

    all_cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    num_cols = ['F', 'G', 'H']

    # Données du budget
    for section in budget.sections.all().order_by('code'):
        # Section
        ws.merge_cells(f'A{row}:E{row}')
        ws[f'A{row}'] = f"{section.code} - {section.libelle}"
        ws[f'F{row}'] = float(section.cout_total_section)
        ws[f'G{row}'] = float(section.co_financement_section)
        ws[f'H{row}'] = float(section.budget_demande_section)
        style_row(row, all_cols, font=section_font, fill=section_fill)
        for col in num_cols:
            ws[f'{col}{row}'].alignment = right
            ws[f'{col}{row}'].number_format = '#,##0'
        row += 1

        for ligne in section.lignes.all().order_by('code'):
            # Ligne budgétaire
            ws.merge_cells(f'A{row}:E{row}')
            ws[f'A{row}'] = f"  {ligne.code} - {ligne.libelle}"
            ws[f'F{row}'] = float(ligne.cout_total_ligne)
            ws[f'G{row}'] = float(ligne.co_financement_ligne)
            ws[f'H{row}'] = float(ligne.budget_demande_ligne)
            style_row(row, all_cols, font=ligne_font, fill=ligne_fill)
            for col in num_cols:
                ws[f'{col}{row}'].alignment = right
                ws[f'{col}{row}'].number_format = '#,##0'
            row += 1

            for groupe in ligne.groupes.all():
                # Groupe
                ws.merge_cells(f'A{row}:E{row}')
                ws[f'A{row}'] = f"    {groupe.libelle}"
                style_row(row, all_cols, font=groupe_font, fill=groupe_fill)
                row += 1

                # Articles
                for article in groupe.articles.all():
                    ws[f'A{row}'] = ""
                    ws[f'B{row}'] = article.designation
                    ws[f'C{row}'] = article.unite
                    ws[f'D{row}'] = float(article.quantite)
                    ws[f'E{row}'] = float(article.prix_unitaire)
                    ws[f'F{row}'] = float(article.cout_total_article)
                    ws[f'G{row}'] = float(article.co_financement)
                    ws[f'H{row}'] = float(article.budget_demande_article)
                    style_row(row, all_cols)
                    for col in ['D', 'E', 'F', 'G', 'H']:
                        ws[f'{col}{row}'].alignment = right
                        ws[f'{col}{row}'].number_format = '#,##0'
                    row += 1

        # Sous-total section
        ws.merge_cells(f'A{row}:E{row}')
        ws[f'A{row}'] = f"Sous total {section.code}"
        ws[f'F{row}'] = float(section.cout_total_section)
        ws[f'G{row}'] = float(section.co_financement_section)
        ws[f'H{row}'] = float(section.budget_demande_section)
        style_row(row, all_cols, font=bold_font, fill=subtotal_fill)
        for col in num_cols:
            ws[f'{col}{row}'].alignment = right
            ws[f'{col}{row}'].number_format = '#,##0'
        row += 1

        # Effectif total apprenant
        ws.merge_cells(f'A{row}:E{row}')
        ws[f'A{row}'] = "Effectif total apprenant"
        ws[f'A{row}'].alignment = center
        ws[f'F{row}'] = budget.total_apprenants
        ws[f'G{row}'] = budget.total_apprenants
        ws[f'H{row}'] = budget.total_apprenants
        style_row(row, all_cols, font=bold_font, fill=green_fill)
        for col in num_cols:
            ws[f'{col}{row}'].alignment = right
        row += 1

        # Coût unitaire par apprenant
        ws.merge_cells(f'A{row}:E{row}')
        ws[f'A{row}'] = "Coût unitaire par apprenant (FCFA)"
        ws[f'A{row}'].alignment = center
        total_app = budget.total_apprenants or 1
        ws[f'F{row}'] = float(section.cout_total_section / total_app)
        ws[f'G{row}'] = float(section.co_financement_section / total_app)
        ws[f'H{row}'] = float(section.budget_demande_section / total_app)
        style_row(row, all_cols, font=bold_font, fill=green_fill)
        for col in num_cols:
            ws[f'{col}{row}'].alignment = right
            ws[f'{col}{row}'].number_format = '#,##0'
        row += 1

    # ===== SYNTHESE FINALE =====
    # Titre SYNTHESE
    ws.merge_cells(f'A{row}:H{row}')
    ws[f'A{row}'] = "SYNTHESE"
    ws[f'A{row}'].font = Font(bold=True, size=12)
    ws[f'A{row}'].alignment = center
    style_row(row, all_cols, font=Font(bold=True, size=12), fill=synthese_title_fill)
    row += 1

    total_app = budget.total_apprenants or 1
    total_sessions = budget.nombre_sessions or 1
    co_fin_pct = (float(budget.co_financement_global) / float(budget.cout_total_global) * 100) if budget.cout_total_global else 0
    budget_pct = (float(budget.budget_demande_global) / float(budget.cout_total_global) * 100) if budget.cout_total_global else 0

    synthese_rows = [
        ("COUT TOTAL/BUDGET (A+B)", float(budget.cout_total_global), float(budget.co_financement_global), float(budget.budget_demande_global), synthese_info_fill, '#,##0'),
        ("%", "", f"{co_fin_pct:.0f}%", f"{budget_pct:.0f}%", None, None),
        ("EFFECTIF TOTAL APPRENANT", budget.total_apprenants, budget.total_apprenants, budget.total_apprenants, None, '#,##0'),
        ("COUT UNITAIRE TOTAL /APPRENANT (FCFA)", float(budget.cout_par_apprenant), float(budget.co_financement_global / total_app), float(budget.budget_demande_global / total_app), synthese_warn_fill, '#,##0'),
        ("Nombre de session", budget.nombre_sessions, budget.nombre_sessions, budget.nombre_sessions, None, None),
        ("Nombre d'apprenant/Session", float(budget.apprenants_par_session), float(budget.apprenants_par_session), float(budget.apprenants_par_session), None, '#,##0'),
        ("Coût total/Session", float(budget.cout_par_session), float(budget.co_financement_global / total_sessions), float(budget.budget_demande_global / total_sessions), synthese_success_fill, '#,##0'),
    ]

    for label, f_val, g_val, h_val, fill, nf in synthese_rows:
        ws.merge_cells(f'A{row}:E{row}')
        ws[f'A{row}'] = label
        ws[f'A{row}'].alignment = center
        ws[f'F{row}'] = f_val
        ws[f'G{row}'] = g_val
        ws[f'H{row}'] = h_val
        style_row(row, all_cols, font=bold_font, fill=fill)
        for col in num_cols:
            ws[f'{col}{row}'].alignment = right
            if nf:
                ws[f'{col}{row}'].number_format = nf
        row += 1

    # Largeurs colonnes
    column_widths = [8, 40, 10, 10, 15, 15, 18, 18]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"Budget_{budget.titre_projet.replace(' ', '_')}_{budget.uuid}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@login_required
def export_pdf(request, uuid):
    """Exporte un budget en format PDF (réservé aux admins)"""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponse("Accès non autorisé", status=403)

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from io import BytesIO

    budget = get_object_or_404(InfosBudget, uuid=uuid)
    budget.calculer_synthese()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        rightMargin=1*cm, leftMargin=1*cm,
        topMargin=1*cm, bottomMargin=1*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
        fontSize=16, textColor=colors.HexColor('#667eea'), alignment=TA_CENTER, spaceAfter=12)

    elements = []
    elements.append(Paragraph(f"BUDGET - {budget.titre_projet}", title_style))
    elements.append(Spacer(1, 0.3*cm))

    # Infos générales
    info_data = [
        ["Opérateur:", str(budget.operateur)],
        ["Filière:", str(budget.filiere) if budget.filiere else ""],
        ["Apprenants:", f"{budget.total_apprenants}          Sessions: {budget.nombre_sessions}"],
    ]
    info_table = Table(info_data, colWidths=[3*cm, 24*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.5*cm))

    # Couleurs
    c_dark = colors.HexColor('#343a40')
    c_grey = colors.HexColor('#6c757d')
    c_info = colors.HexColor('#d1ecf1')
    c_warning = colors.HexColor('#fff3cd')
    c_green = colors.HexColor('#d4edda')
    c_primary = colors.HexColor('#b8daff')
    c_success = colors.HexColor('#c3e6cb')
    c_header = colors.HexColor('#667eea')

    # Tableau budget
    data = [["Code", "Désignation", "Unité", "Qté", "Prix Unit.", "Coût Total", "Co-financement", "Budget demandé"]]

    # Tracking des indices pour le style
    row_styles = {}  # index -> (bg_color, text_color, bold)

    def add_row(values, bg=None, fg=colors.black, bold=False):
        idx = len(data)
        data.append(values)
        if bg or bold:
            row_styles[idx] = (bg, fg, bold)

    for section in budget.sections.all().order_by('code'):
        add_row([section.code, section.libelle, "", "", "",
                 f"{section.cout_total_section:,.0f}", f"{section.co_financement_section:,.0f}",
                 f"{section.budget_demande_section:,.0f}"], bg=c_dark, fg=colors.white, bold=True)

        for ligne in section.lignes.all().order_by('code'):
            add_row([ligne.code, ligne.libelle, "", "", "",
                     f"{ligne.cout_total_ligne:,.0f}", f"{ligne.co_financement_ligne:,.0f}",
                     f"{ligne.budget_demande_ligne:,.0f}"], bg=c_grey, fg=colors.white, bold=True)

            for groupe in ligne.groupes.all():
                add_row(["", f"  {groupe.libelle}", "", "", "", "", "", ""],
                        bg=c_info, bold=True)

                for article in groupe.articles.all():
                    add_row(["", f"    {article.designation}", article.unite or "",
                             f"{article.quantite:,.2f}", f"{article.prix_unitaire:,.0f}",
                             f"{article.cout_total_article:,.0f}", f"{article.co_financement:,.0f}",
                             f"{article.budget_demande_article:,.0f}"])

        # Sous-total section
        total_app = budget.total_apprenants or 1
        add_row([f"Sous total {section.code}", "", "", "", "",
                 f"{section.cout_total_section:,.0f}", f"{section.co_financement_section:,.0f}",
                 f"{section.budget_demande_section:,.0f}"], bg=c_warning, bold=True)

        add_row(["Effectif total apprenant", "", "", "", "",
                 str(budget.total_apprenants), str(budget.total_apprenants),
                 str(budget.total_apprenants)], bg=c_green, bold=True)

        cout_unit = float(section.cout_total_section / total_app)
        cofin_unit = float(section.co_financement_section / total_app)
        bud_unit = float(section.budget_demande_section / total_app)
        add_row(["Coût unitaire par apprenant (FCFA)", "", "", "", "",
                 f"{cout_unit:,.0f}", f"{cofin_unit:,.0f}", f"{bud_unit:,.0f}"],
                bg=c_green, bold=True)

    # SYNTHESE FINALE
    add_row(["SYNTHESE", "", "", "", "", "", "", ""], bg=c_primary, bold=True)

    total_app = budget.total_apprenants or 1
    total_sessions = budget.nombre_sessions or 1
    co_fin_pct = (float(budget.co_financement_global) / float(budget.cout_total_global) * 100) if budget.cout_total_global else 0
    budget_pct = (float(budget.budget_demande_global) / float(budget.cout_total_global) * 100) if budget.cout_total_global else 0

    add_row(["COUT TOTAL/BUDGET (A+B)", "", "", "", "",
             f"{budget.cout_total_global:,.0f}", f"{budget.co_financement_global:,.0f}",
             f"{budget.budget_demande_global:,.0f}"], bg=c_info, bold=True)

    add_row(["%", "", "", "", "", "", f"{co_fin_pct:.0f}%", f"{budget_pct:.0f}%"], bold=True)

    add_row(["EFFECTIF TOTAL APPRENANT", "", "", "", "",
             str(budget.total_apprenants), str(budget.total_apprenants),
             str(budget.total_apprenants)], bold=True)

    add_row(["COUT UNITAIRE TOTAL /APPRENANT (FCFA)", "", "", "", "",
             f"{budget.cout_par_apprenant:,.0f}",
             f"{float(budget.co_financement_global / total_app):,.0f}",
             f"{float(budget.budget_demande_global / total_app):,.0f}"],
            bg=c_warning, bold=True)

    add_row(["Nombre de session", "", "", "", "",
             str(budget.nombre_sessions), str(budget.nombre_sessions),
             str(budget.nombre_sessions)], bold=True)

    add_row(["Nombre d'apprenant/Session", "", "", "", "",
             f"{float(budget.apprenants_par_session):,.0f}",
             f"{float(budget.apprenants_par_session):,.0f}",
             f"{float(budget.apprenants_par_session):,.0f}"], bold=True)

    add_row(["Coût total/Session", "", "", "", "",
             f"{float(budget.cout_par_session):,.0f}",
             f"{float(budget.co_financement_global / total_sessions):,.0f}",
             f"{float(budget.budget_demande_global / total_sessions):,.0f}"],
            bg=c_success, bold=True)

    # Créer le tableau
    col_widths = [2*cm, 6*cm, 1.5*cm, 1.5*cm, 2.5*cm, 3*cm, 3*cm, 3*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)

    table_style_list = [
        ('BACKGROUND', (0, 0), (-1, 0), c_header),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]

    for idx, (bg, fg, bold) in row_styles.items():
        if bg:
            table_style_list.append(('BACKGROUND', (0, idx), (-1, idx), bg))
        if fg != colors.black:
            table_style_list.append(('TEXTCOLOR', (0, idx), (-1, idx), fg))
        if bold:
            table_style_list.append(('FONTNAME', (0, idx), (-1, idx), 'Helvetica-Bold'))

    table.setStyle(TableStyle(table_style_list))
    elements.append(table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    filename = f"Budget_{budget.titre_projet.replace(' ', '_')}_{budget.uuid}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf)
    return response


@login_required
def export_word(request, uuid):
    """Exporte un budget en format Word (réservé aux admins)"""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponse("Accès non autorisé", status=403)

    from docx import Document
    from docx.shared import Inches, Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    from io import BytesIO

    budget = get_object_or_404(InfosBudget, uuid=uuid)
    budget.calculer_synthese()

    doc = Document()

    # Page en paysage
    section = doc.sections[0]
    section.page_width, section.page_height = section.page_height, section.page_width
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)

    def set_cell_bg(cell, color_hex):
        """Applique une couleur de fond à une cellule Word"""
        shading = OxmlElement('w:shd')
        shading.set(qn('w:fill'), color_hex)
        shading.set(qn('w:val'), 'clear')
        cell._tc.get_or_add_tcPr().append(shading)

    def set_cell_text(cell, text, bold=False, size=8, align='left', color=None):
        """Configure le texte d'une cellule"""
        cell.text = ""
        p = cell.paragraphs[0]
        if align == 'right':
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif align == 'center':
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(str(text))
        run.font.size = Pt(size)
        run.font.bold = bold
        if color:
            run.font.color.rgb = color

    def style_row_cells(row_cells, text_values, bold=False, bg_color=None, text_color=None, size=8):
        """Style une ligne complète du tableau"""
        for i, (cell, val) in enumerate(zip(row_cells, text_values)):
            align = 'right' if i >= 5 else 'left'
            set_cell_text(cell, val, bold=bold, size=size, align=align, color=text_color)
            if bg_color:
                set_cell_bg(cell, bg_color)

    # Titre
    title = doc.add_heading(f'BUDGET - {budget.titre_projet}', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.runs[0].font.color.rgb = RGBColor(102, 126, 234)

    # Informations générales
    info_table = doc.add_table(rows=3, cols=2)
    info_table.style = 'Table Grid'
    info_data = [
        ("Opérateur:", str(budget.operateur)),
        ("Filière:", str(budget.filiere) if budget.filiere else ""),
        ("Apprenants:", f"{budget.total_apprenants}     |     Sessions: {budget.nombre_sessions}"),
    ]
    for i, (label, val) in enumerate(info_data):
        set_cell_text(info_table.rows[i].cells[0], label, bold=True, size=9)
        set_cell_text(info_table.rows[i].cells[1], val, size=9)

    doc.add_paragraph()

    # Tableau budget
    headers = ["Code", "Désignation", "Unité", "Qté", "Prix Unit.", "Coût Total", "Co-financement", "Budget demandé"]
    table = doc.add_table(rows=1, cols=8)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # En-têtes
    for i, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], header, bold=True, size=8, align='center',
                      color=RGBColor(255, 255, 255))
        set_cell_bg(table.rows[0].cells[i], '667eea')

    white = RGBColor(255, 255, 255)

    for sec in budget.sections.all().order_by('code'):
        # Section
        r = table.add_row().cells
        style_row_cells(r, [sec.code, sec.libelle, "", "", "",
            f"{sec.cout_total_section:,.0f}", f"{sec.co_financement_section:,.0f}",
            f"{sec.budget_demande_section:,.0f}"], bold=True, bg_color='343a40', text_color=white)

        for ligne in sec.lignes.all().order_by('code'):
            # Ligne budgétaire
            r = table.add_row().cells
            style_row_cells(r, [ligne.code, ligne.libelle, "", "", "",
                f"{ligne.cout_total_ligne:,.0f}", f"{ligne.co_financement_ligne:,.0f}",
                f"{ligne.budget_demande_ligne:,.0f}"], bold=True, bg_color='6c757d', text_color=white)

            for groupe in ligne.groupes.all():
                # Groupe
                r = table.add_row().cells
                style_row_cells(r, ["", groupe.libelle, "", "", "", "", "", ""],
                                bold=True, bg_color='d1ecf1')

                # Articles
                for article in groupe.articles.all():
                    r = table.add_row().cells
                    style_row_cells(r, ["", f"  {article.designation}", article.unite or "",
                        f"{article.quantite:,.2f}", f"{article.prix_unitaire:,.0f}",
                        f"{article.cout_total_article:,.0f}", f"{article.co_financement:,.0f}",
                        f"{article.budget_demande_article:,.0f}"])

        # Sous-total section
        total_app = budget.total_apprenants or 1
        r = table.add_row().cells
        style_row_cells(r, [f"Sous total {sec.code}", "", "", "", "",
            f"{sec.cout_total_section:,.0f}", f"{sec.co_financement_section:,.0f}",
            f"{sec.budget_demande_section:,.0f}"], bold=True, bg_color='fff3cd')

        r = table.add_row().cells
        style_row_cells(r, ["Effectif total apprenant", "", "", "", "",
            str(budget.total_apprenants), str(budget.total_apprenants),
            str(budget.total_apprenants)], bold=True, bg_color='d4edda')

        r = table.add_row().cells
        style_row_cells(r, ["Coût unitaire par apprenant (FCFA)", "", "", "", "",
            f"{float(sec.cout_total_section / total_app):,.0f}",
            f"{float(sec.co_financement_section / total_app):,.0f}",
            f"{float(sec.budget_demande_section / total_app):,.0f}"], bold=True, bg_color='d4edda')

    # SYNTHESE FINALE
    r = table.add_row().cells
    style_row_cells(r, ["SYNTHESE", "", "", "", "", "", "", ""],
                    bold=True, bg_color='b8daff', size=10)

    total_app = budget.total_apprenants or 1
    total_sessions = budget.nombre_sessions or 1
    co_fin_pct = (float(budget.co_financement_global) / float(budget.cout_total_global) * 100) if budget.cout_total_global else 0
    budget_pct = (float(budget.budget_demande_global) / float(budget.cout_total_global) * 100) if budget.cout_total_global else 0

    r = table.add_row().cells
    style_row_cells(r, ["COUT TOTAL/BUDGET (A+B)", "", "", "", "",
        f"{budget.cout_total_global:,.0f}", f"{budget.co_financement_global:,.0f}",
        f"{budget.budget_demande_global:,.0f}"], bold=True, bg_color='d1ecf1')

    r = table.add_row().cells
    style_row_cells(r, ["%", "", "", "", "", "", f"{co_fin_pct:.0f}%", f"{budget_pct:.0f}%"], bold=True)

    r = table.add_row().cells
    style_row_cells(r, ["EFFECTIF TOTAL APPRENANT", "", "", "", "",
        str(budget.total_apprenants), str(budget.total_apprenants),
        str(budget.total_apprenants)], bold=True)

    r = table.add_row().cells
    style_row_cells(r, ["COUT UNITAIRE TOTAL /APPRENANT (FCFA)", "", "", "", "",
        f"{budget.cout_par_apprenant:,.0f}",
        f"{float(budget.co_financement_global / total_app):,.0f}",
        f"{float(budget.budget_demande_global / total_app):,.0f}"], bold=True, bg_color='fff3cd')

    r = table.add_row().cells
    style_row_cells(r, ["Nombre de session", "", "", "", "",
        str(budget.nombre_sessions), str(budget.nombre_sessions),
        str(budget.nombre_sessions)], bold=True)

    r = table.add_row().cells
    style_row_cells(r, ["Nombre d'apprenant/Session", "", "", "", "",
        f"{float(budget.apprenants_par_session):,.0f}",
        f"{float(budget.apprenants_par_session):,.0f}",
        f"{float(budget.apprenants_par_session):,.0f}"], bold=True)

    r = table.add_row().cells
    style_row_cells(r, ["Coût total/Session", "", "", "", "",
        f"{float(budget.cout_par_session):,.0f}",
        f"{float(budget.co_financement_global / total_sessions):,.0f}",
        f"{float(budget.budget_demande_global / total_sessions):,.0f}"], bold=True, bg_color='c3e6cb')

    # Sauvegarder
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    filename = f"Budget_{budget.titre_projet.replace(' ', '_')}_{budget.uuid}.docx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ========================= PROFIL & MOT DE PASSE =========================

@login_required
def _style_password_form(form):
    """Ajoute la classe form-control aux champs du formulaire de mot de passe."""
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    return form

@login_required
def profil(request):
    """Page de profil de l'utilisateur"""
    return render(request, 'budgets/profil.html', {
        'user': request.user,
        'password_form': _style_password_form(PasswordChangeForm(request.user)),
    })

@login_required
def changer_mot_de_passe(request):
    """Permet à l'utilisateur de changer son mot de passe"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Votre mot de passe a été changé avec succès !')
            return redirect('budgets:profil')
        else:
            # Erreur : réafficher le profil avec le modal ouvert
            return render(request, 'budgets/profil.html', {
                'password_form': _style_password_form(form),
                'show_password_modal': True,
            })

    return redirect('budgets:profil')

# ========================= WORKFLOW DE VALIDATION =========================

@login_required
def soumettre_budget(request, uuid):
    """Soumet le budget pour validation par l'admin"""
    from django.utils import timezone
    budget = get_object_or_404(InfosBudget, uuid=uuid)

    # Vérifier que l'utilisateur est le créateur ou admin
    if budget.created_by != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Vous n'avez pas la permission de soumettre ce budget.")
        return redirect('budgets:budget_detail', uuid=uuid)

    # Vérifier que le budget est modifiable (brouillon, soumis avec appel actif, ou modification autorisée)
    if not budget.peut_etre_modifie():
        messages.error(request, "Ce budget ne peut pas être soumis dans son état actuel.")
        return redirect('budgets:budget_detail', uuid=uuid)

    # Recalculer la synthèse et vérifier la règle des 30% pour A.1
    budget.calculer_synthese()
    budget.refresh_from_db()
    valide, erreur = budget.verifier_validation_a1()
    if not valide:
        messages.error(request, erreur)
        return redirect('budgets:budget_detail', uuid=uuid)

    # Mettre à jour le statut
    budget.statut = InfosBudget.STATUT_SOUMIS
    budget.date_soumission = timezone.now()
    budget.save()

    # Envoyer un email à l'admin (en arrière-plan)
    admin_emails = [u.email for u in User.objects.filter(is_staff=True, is_active=True) if u.email]
    if admin_emails:
        _envoyer_email_async(
            subject=f'Nouveau budget soumis: {budget.titre_projet}',
            message=f"""Un nouveau budget a été soumis pour validation.

Titre du projet: {budget.titre_projet}
Opérateur: {budget.operateur}
Filière: {budget.filiere if budget.filiere else 'Non spécifiée'}
Soumis par: {budget.created_by.username if budget.created_by else 'Inconnu'}
Date de soumission: {timezone.now().strftime('%d/%m/%Y %H:%M')}

Coût total global: {budget.cout_total_global:,.0f} FCFA
Budget demandé: {budget.budget_demande_global:,.0f} FCFA

Veuillez vous connecter à l'application pour examiner ce budget.""",
            recipient_list=admin_emails,
        )

    messages.success(request, "Votre budget a été soumis avec succès. Vous recevrez une notification une fois qu'il aura été examiné.")
    return redirect('budgets:budget_detail', uuid=uuid)

@login_required
def demander_modification(request, uuid):
    """Admin demande à l'opérateur de modifier son budget (avec motif + email)"""
    from django.utils import timezone
    # Réservé aux admins
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Accès non autorisé.")
        return redirect('budgets:dashboard')

    budget = get_object_or_404(InfosBudget, uuid=uuid)

    # Vérifier que le budget est soumis
    if budget.statut != InfosBudget.STATUT_SOUMIS:
        messages.error(request, "Seuls les budgets soumis peuvent faire l'objet d'une demande de modification.")
        return redirect('budgets:budget_detail', uuid=uuid)

    if request.method == 'POST':
        motif = request.POST.get('motif', '').strip()
        if not motif:
            messages.error(request, "Veuillez indiquer le motif de la demande de modification.")
            return render(request, 'budgets/demander_modification.html', {'budget': budget})

        # Passer directement en modification autorisée
        budget.statut = InfosBudget.STATUT_MODIFICATION_AUTORISEE
        budget.motif_demande_modification = motif
        budget.date_demande_modification = timezone.now()
        budget.date_autorisation_modification = timezone.now()
        budget.save()

        # Envoyer un email à l'opérateur (en arrière-plan)
        budget_url = request.build_absolute_uri(f'/budgets/{budget.uuid}/')
        if budget.created_by and budget.created_by.email:
            _envoyer_email_async(
                subject=f'[MODIFICATION DEMANDÉE] {budget.titre_projet}',
                message=f"""Bonjour {budget.created_by.get_full_name() or budget.created_by.username},

L'administrateur vous demande de modifier votre budget "{budget.titre_projet}".

Motif de la demande :
{motif}

Vous pouvez maintenant modifier votre budget et le soumettre à nouveau.

Cliquez ici pour accéder à votre budget :
{budget_url}

Cordialement,
Système de Gestion de Budget""",
                recipient_list=[budget.created_by.email],
            )

        messages.success(request, "La demande de modification a été envoyée à l'opérateur par email. Le budget est maintenant modifiable.")
        return redirect('budgets:budget_detail', uuid=uuid)

    return render(request, 'budgets/demander_modification.html', {'budget': budget})

@login_required
def approuver_budget(request, uuid):
    """Admin approuve définitivement un budget (vue admin uniquement)"""
    from django.utils import timezone
    # Vérifier que l'utilisateur est admin
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Accès non autorisé - Seuls les administrateurs peuvent approuver des budgets.")
        return redirect('budgets:dashboard')

    budget = get_object_or_404(InfosBudget, uuid=uuid)

    # Vérifier que le budget est soumis
    if budget.statut != InfosBudget.STATUT_SOUMIS:
        messages.error(request, "Seuls les budgets soumis peuvent être approuvés.")
        return redirect('budgets:budget_detail', uuid=uuid)

    # Approuver le budget
    budget.statut = InfosBudget.STATUT_APPROUVE
    budget.date_approbation = timezone.now()
    budget.save()

    # Envoyer un email au créateur (en arrière-plan)
    if budget.created_by and budget.created_by.email:
        _envoyer_email_async(
            subject=f'Budget approuvé: {budget.titre_projet}',
            message=f"""Félicitations! Votre budget "{budget.titre_projet}" a été approuvé.

Coût total global: {budget.cout_total_global:,.0f} FCFA
Budget demandé: {budget.budget_demande_global:,.0f} FCFA
Date d'approbation: {timezone.now().strftime('%d/%m/%Y %H:%M')}

Merci pour votre soumission.""",
            recipient_list=[budget.created_by.email],
        )

    messages.success(request, "Le budget a été approuvé. L'opérateur a été notifié.")
    return redirect('budgets:budget_detail', uuid=uuid)

@login_required
def rejeter_budget(request, uuid):
    """Admin rejette définitivement un budget"""
    from django.utils import timezone
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Accès non autorisé.")
        return redirect('budgets:dashboard')

    budget = get_object_or_404(InfosBudget, uuid=uuid)

    if budget.statut != InfosBudget.STATUT_SOUMIS:
        messages.error(request, "Seuls les budgets soumis peuvent être rejetés.")
        return redirect('budgets:budget_detail', uuid=uuid)

    budget.statut = InfosBudget.STATUT_REJETE
    budget.save()

    # Envoyer un email à l'opérateur (en arrière-plan)
    if budget.created_by and budget.created_by.email:
        _envoyer_email_async(
            subject=f'Budget rejeté: {budget.titre_projet}',
            message=f"""Bonjour {budget.created_by.get_full_name() or budget.created_by.username},

Votre budget "{budget.titre_projet}" a été rejeté par l'administrateur.

Coût total global: {budget.cout_total_global:,.0f} FCFA
Budget demandé: {budget.budget_demande_global:,.0f} FCFA

Pour toute question, veuillez contacter l'administrateur.

Cordialement,
Système de Gestion de Budget""",
            recipient_list=[budget.created_by.email],
        )

    messages.success(request, "Le budget a été rejeté. L'opérateur a été notifié.")
    return redirect('budgets:budget_detail', uuid=uuid)

