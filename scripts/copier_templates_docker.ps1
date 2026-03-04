# Script PowerShell pour copier les templates depuis l'hôte vers le conteneur Docker

Write-Host "📋 Copie des templates vers le conteneur Docker..." -ForegroundColor Cyan

# Vérifier que le fichier source existe
$SOURCE_FILE = "media\templates\template_budget.xlsx"
if (-not (Test-Path $SOURCE_FILE)) {
    Write-Host "❌ Erreur: Le fichier $SOURCE_FILE n'existe pas" -ForegroundColor Red
    exit 1
}

# Nom du conteneur
$CONTAINER_NAME = "budget_web"

# Vérifier que le conteneur est en cours d'exécution
$containerRunning = docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}"
if (-not $containerRunning) {
    Write-Host "❌ Erreur: Le conteneur $CONTAINER_NAME n'est pas en cours d'exécution" -ForegroundColor Red
    Write-Host "💡 Démarrez le conteneur avec: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

# Créer le dossier de destination dans le conteneur
Write-Host "📁 Création du dossier de destination..." -ForegroundColor Cyan
docker exec $CONTAINER_NAME mkdir -p /app/media/templates

# Copier le fichier
Write-Host "📁 Copie de $SOURCE_FILE vers le conteneur..." -ForegroundColor Cyan
docker cp $SOURCE_FILE "${CONTAINER_NAME}:/app/media/templates/"

# Copier tous les autres fichiers du dossier templates
if (Test-Path "media\templates") {
    Write-Host "📁 Copie de tous les fichiers templates..." -ForegroundColor Cyan
    Get-ChildItem -Path "media\templates" -File | ForEach-Object {
        $filename = $_.Name
        docker cp $_.FullName "${CONTAINER_NAME}:/app/media/templates/$filename"
        Write-Host "   ✅ Copié: $filename" -ForegroundColor Green
    }
}

Write-Host "✅ Templates copiés avec succès!" -ForegroundColor Green
Write-Host "💡 Vous pouvez maintenant tester le téléchargement" -ForegroundColor Yellow
