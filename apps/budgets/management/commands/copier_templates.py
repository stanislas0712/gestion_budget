from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import shutil
import os


class Command(BaseCommand):
    help = 'Copie les templates depuis le code source vers MEDIA_ROOT/templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default=None,
            help='Chemin source des templates (par défaut: cherche dans le projet)',
        )

    def handle(self, *args, **options):
        source_path = options.get('source')
        destination = Path(settings.MEDIA_ROOT) / 'templates'
        destination.mkdir(parents=True, exist_ok=True)
        
        # Vérifier si les templates sont déjà dans la destination
        if (destination / 'template_budget.xlsx').exists():
            self.stdout.write(
                self.style.SUCCESS('✅ Templates déjà présents dans MEDIA_ROOT/templates')
            )
            return
        
        # Si un chemin source est fourni, l'utiliser
        if source_path:
            source_found = Path(source_path)
            if not source_found.exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ Le chemin source n\'existe pas: {source_path}')
                )
                return
            if not (source_found / 'template_budget.xlsx').exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ Le fichier template_budget.xlsx n\'existe pas dans: {source_path}')
                )
                return
        else:
            # Chercher les templates dans plusieurs emplacements possibles
            # Note: Dans Docker, le volume peut masquer le dossier source
            source_dirs = [
                Path(settings.BASE_DIR) / 'media' / 'templates',
                Path(__file__).parent.parent.parent.parent.parent / 'media' / 'templates',
            ]
            
            # Essayer aussi de trouver via le chemin absolu du fichier actuel
            current_file = Path(__file__).resolve()
            # Remonter depuis apps/budgets/management/commands/ vers la racine
            project_root = current_file.parent.parent.parent.parent.parent
            source_dirs.append(project_root / 'media' / 'templates')
            
            source_found = None
            for source_dir in source_dirs:
                template_file = source_dir / 'template_budget.xlsx'
                if template_file.exists():
                    source_found = source_dir
                    break
            
            if not source_found:
                # Dernière tentative : chercher dans tout le projet (sauf dans media qui peut être masqué)
                self.stdout.write('🔍 Recherche des templates dans le projet...')
                for root, dirs, files in os.walk(settings.BASE_DIR):
                    # Ignorer le dossier media qui peut être masqué par un volume
                    if 'media' in root.split(os.sep) and root != str(settings.BASE_DIR / 'media'):
                        continue
                    if 'template_budget.xlsx' in files:
                        source_found = Path(root)
                        break
                
                # Si toujours pas trouvé, essayer de chercher dans le code source monté
                # En Docker, le code source est monté sur /app, mais media peut être masqué
                # On peut essayer de chercher via le chemin du fichier Python actuel
                if not source_found:
                    # Chercher dans le répertoire parent du projet (code source hôte)
                    # En Docker, le code source est monté, donc on peut essayer de remonter
                    try:
                        # Le fichier est dans apps/budgets/management/commands/
                        # On remonte: commands -> management -> budgets -> apps -> racine
                        cmd_file = Path(__file__).resolve()
                        # Dans Docker, le code source est monté sur /app
                        # On peut essayer de trouver le fichier en remontant depuis le fichier actuel
                        possible_roots = [
                            cmd_file.parent.parent.parent.parent.parent,  # 5 niveaux
                            cmd_file.parent.parent.parent.parent.parent.parent,  # 6 niveaux
                        ]
                        for root in possible_roots:
                            test_path = root / 'media' / 'templates' / 'template_budget.xlsx'
                            if test_path.exists():
                                source_found = root / 'media' / 'templates'
                                self.stdout.write(f'📋 Template trouvé via chemin relatif: {source_found}')
                                break
                    except Exception as e:
                        self.stdout.write(f'⚠️  Erreur lors de la recherche: {e}')
        
        if not source_found:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Aucun template trouvé.\n'
                    f'   Vérifiez que le fichier template_budget.xlsx existe dans media/templates/'
                )
            )
            return
        
        self.stdout.write(f'📋 Source trouvée: {source_found}')
        self.stdout.write(f'📁 Destination: {destination}')
        
        # Copier tous les fichiers templates
        fichiers_copies = 0
        for fichier in source_found.glob('*'):
            if fichier.is_file() and not fichier.name.startswith('.'):
                dest_file = destination / fichier.name
                try:
                    shutil.copy2(fichier, dest_file)
                    fichiers_copies += 1
                    self.stdout.write(f'   ✅ Copié: {fichier.name}')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Erreur lors de la copie de {fichier.name}: {e}')
                    )
        
        if fichiers_copies > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {fichiers_copies} fichier(s) copié(s) avec succès vers {destination}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  Aucun fichier copié')
            )
