# Script PowerShell pour restaurer une sauvegarde de la base de données PostgreSQL

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile
)

Write-Host "🔄 Restauration de la base de données PostgreSQL..." -ForegroundColor Cyan

# Vérifier que le fichier de sauvegarde existe
if (-not (Test-Path $BackupFile)) {
    Write-Host "❌ Le fichier de sauvegarde n'existe pas: $BackupFile" -ForegroundColor Red
    exit 1
}

# Vérifier que le conteneur db existe et est en cours d'exécution
$containerRunning = docker ps --filter "name=budget_db" --format "{{.Names}}"
if (-not $containerRunning) {
    Write-Host "⚠️  Le conteneur budget_db n'est pas en cours d'exécution. Démarrage..." -ForegroundColor Yellow
    docker start budget_db
    Start-Sleep -Seconds 5
}

# Récupérer les variables d'environnement depuis .env
$envFile = ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "❌ Le fichier .env n'existe pas!" -ForegroundColor Red
    exit 1
}

$dbName = "budget"
$dbUser = "budget"
$dbPassword = "budget"

Get-Content $envFile | ForEach-Object {
    if ($_ -match "^DB_NAME=(.+)$") {
        $dbName = $matches[1].Trim()
    }
    if ($_ -match "^DB_USER=(.+)$") {
        $dbUser = $matches[1].Trim()
    }
    if ($_ -match "^DB_PASSWORD=(.+)$") {
        $dbPassword = $matches[1].Trim()
    }
}

Write-Host "📊 Base de données: $dbName" -ForegroundColor Cyan
Write-Host "👤 Utilisateur: $dbUser" -ForegroundColor Cyan
Write-Host "📁 Fichier de sauvegarde: $BackupFile" -ForegroundColor Cyan

# Confirmation
$confirm = Read-Host "⚠️  Cette opération va ÉCRASER toutes les données actuelles. Continuer? (oui/non)"
if ($confirm -ne "oui" -and $confirm -ne "o" -and $confirm -ne "yes" -and $confirm -ne "y") {
    Write-Host "❌ Opération annulée." -ForegroundColor Yellow
    exit 0
}

# Restaurer la sauvegarde
Write-Host "🔄 Restauration en cours..." -ForegroundColor Yellow

$env:PGPASSWORD = $dbPassword

# Si le fichier est compressé, le décompresser d'abord
if ($BackupFile -match "\.gz$") {
    Write-Host "📦 Décompression du fichier..." -ForegroundColor Yellow
    $tempFile = $BackupFile -replace "\.gz$", ""
    if (Get-Command gunzip -ErrorAction SilentlyContinue) {
        gunzip -c $BackupFile | docker exec -i budget_db psql -U $dbUser -d $dbName
    } else {
        Write-Host "❌ gunzip non disponible. Décompressez manuellement le fichier .gz" -ForegroundColor Red
        exit 1
    }
} else {
    Get-Content $BackupFile -Encoding UTF8 | docker exec -i budget_db psql -U $dbUser -d $dbName
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Restauration terminée avec succès!" -ForegroundColor Green
} else {
    Write-Host "❌ Erreur lors de la restauration!" -ForegroundColor Red
    exit 1
}
