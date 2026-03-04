# Script PowerShell pour sauvegarder la base de données PostgreSQL avant toute manipulation

Write-Host "💾 Sauvegarde de la base de données PostgreSQL..." -ForegroundColor Cyan

# Créer le dossier de sauvegarde s'il n'existe pas
$backupDir = "backups"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

# Nom du fichier de sauvegarde avec timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$backupDir/budget_db_backup_$timestamp.sql"
$backupFileCompressed = "$backupFile.gz"

Write-Host "📁 Fichier de sauvegarde: $backupFile" -ForegroundColor Yellow

# Vérifier que le conteneur db existe
$containerExists = docker ps -a --filter "name=budget_db" --format "{{.Names}}"
if (-not $containerExists) {
    Write-Host "❌ Le conteneur budget_db n'existe pas!" -ForegroundColor Red
    exit 1
}

# Vérifier si le conteneur est en cours d'exécution
$containerRunning = docker ps --filter "name=budget_db" --format "{{.Names}}"
if (-not $containerRunning) {
    Write-Host "⚠️  Le conteneur n'est pas en cours d'exécution. Tentative de démarrage..." -ForegroundColor Yellow
    docker start budget_db
    Start-Sleep -Seconds 5
}

# Récupérer les variables d'environnement depuis .env
$envFile = ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "❌ Le fichier .env n'existe pas!" -ForegroundColor Red
    exit 1
}

# Lire les variables depuis .env
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

# Créer la sauvegarde
Write-Host "🔄 Création de la sauvegarde..." -ForegroundColor Yellow

$env:PGPASSWORD = $dbPassword
$result = docker exec budget_db pg_dump -U $dbUser -d $dbName -F p 2>&1 | Out-File -FilePath $backupFile -Encoding UTF8

if ($LASTEXITCODE -eq 0) {
    $fileSize = (Get-Item $backupFile).Length
    Write-Host "✅ Sauvegarde créée avec succès!" -ForegroundColor Green
    Write-Host "   Taille: $([math]::Round($fileSize / 1MB, 2)) MB" -ForegroundColor Green
    Write-Host "   Fichier: $backupFile" -ForegroundColor Green
    
    # Optionnel: compresser la sauvegarde
    Write-Host "📦 Compression de la sauvegarde..." -ForegroundColor Yellow
    try {
        # Utiliser gzip si disponible (via WSL ou Git Bash)
        if (Get-Command gzip -ErrorAction SilentlyContinue) {
            gzip -k $backupFile
            Write-Host "✅ Sauvegarde compressée: $backupFileCompressed" -ForegroundColor Green
        } else {
            Write-Host "⚠️  gzip non disponible, sauvegarde non compressée" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Impossible de compresser, mais la sauvegarde est valide" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Erreur lors de la création de la sauvegarde!" -ForegroundColor Red
    Write-Host $result -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Sauvegarde terminée! Vous pouvez maintenant procéder en toute sécurité." -ForegroundColor Green
Write-Host "💡 Pour restaurer: .\scripts\restaurer-db.ps1 -BackupFile $backupFile" -ForegroundColor Yellow
