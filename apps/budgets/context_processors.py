from django.utils import timezone


def appel_a_projet_context(request):
    """Fournit l'appel a projet actif a tous les templates."""
    if not request.user.is_authenticated:
        return {}

    from apps.projects.models import AppelAProjet

    now = timezone.now()
    appel = AppelAProjet.objects.filter(
        date_debut__lte=now, date_fin__gte=now
    ).first()

    if not appel:
        return {'appel_global': None}

    # Calculer les jours restants avant la fin
    jours_restants = (appel.date_fin - now).days

    return {
        'appel_global': appel,
        'appel_jours_restants': jours_restants,
        'appel_fin_proche': jours_restants <= 7,
    }