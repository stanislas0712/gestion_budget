"""
Commande Django pour créer rapidement un utilisateur avec un mot de passe simple
Usage: python manage.py creer_utilisateur
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Crée un utilisateur avec un mot de passe simple'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nom d\'utilisateur')
        parser.add_argument('password', type=str, help='Mot de passe (peut être des chiffres uniquement)')
        parser.add_argument(
            '--admin',
            action='store_true',
            help='Créer un utilisateur administrateur (staff)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='',
            help='Adresse email (optionnel)',
        )
        parser.add_argument(
            '--prenom',
            type=str,
            default='',
            help='Prénom (optionnel)',
        )
        parser.add_argument(
            '--nom',
            type=str,
            default='',
            help='Nom de famille (optionnel)',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        is_admin = options['admin']
        email = options['email']
        prenom = options['prenom']
        nom = options['nom']

        # Vérifier si l'utilisateur existe déjà
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'❌ L\'utilisateur "{username}" existe déjà!')
            )
            return

        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=prenom,
            last_name=nom,
        )

        # Définir les permissions si admin
        if is_admin:
            user.is_staff = True
            user.is_superuser = True
            user.save()

        # Message de succès
        type_user = "administrateur" if is_admin else "utilisateur standard"
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ {type_user.capitalize()} créé avec succès!')
        )
        self.stdout.write(f'   👤 Nom d\'utilisateur: {username}')
        self.stdout.write(f'   🔑 Mot de passe: {password}')
        if email:
            self.stdout.write(f'   📧 Email: {email}')
        if prenom or nom:
            self.stdout.write(f'   📝 Nom complet: {prenom} {nom}')
        self.stdout.write(f'   🔐 Type: {type_user}\n')
