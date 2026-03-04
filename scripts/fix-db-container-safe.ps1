# Script PowerShell pour résoudre l'erreur ContainerConfig SANS perdre les données

Write-Host "🔧 Résolution de l'erreur ContainerConfig (mode sécurisé)..." -ForegroundColor Cyan

# Étape 1: Sauvegarder la base de données
Write-Host "`n📋 ÉTAPE 1: Sauvegarde de la base de données" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Yellow

$backupScript = ".\scripts\sauvegarder-db.ps1"
if (Test-Path $backupScript) {
    & $backupScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ La sauvegarde a échoué. Arrêt de la procédure." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  Script de sauvegarde non trouvé. Création d'une sauvegarde manuelle..." -ForegroundColor Yellow
    
    # Sauvegarde manuelle rapide
    $backupDir = "backups"
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir | Out-Null
    }
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "$backupDir/budget_db_backup_$timestamp.sql"
    
    Write-Host "💾 Création de la sauvegarde: $backupFile" -ForegroundColor Yellow
    docker exec budget_db pg_dump -U budget -d budget -F p > $backupFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Sauvegarde créée: $backupFile" -ForegroundColor Green
    } else {
        Write-Host "❌ Échec de la sauvegarde. Arrêt." -ForegroundColor Red
        exit 1
    }
}

# Étape 2: Arrêter les conteneurs dépendants
Write-Host "`n📋 ÉTAPE 2: Arrêt des conteneurs dépendants" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Yellow

Write-Host "🛑 Arrêt des services dépendants..." -ForegroundColor Yellow
docker-compose stop web celery_worker celery_beat 2>$null

# Étape 3: Sauvegarder le volume (optionnel mais recommandé)
Write-Host "`n📋 ÉTAPE 3: Sauvegarde du volume Docker" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Yellow

$volumeBackup = "backups/postgres_volume_$(Get-Date -Format 'yyyyMMdd_HHmmss').tar"
Write-Host "💾 Sauvegarde du volume postgres_data..." -ForegroundColor Yellow

# Créer un conteneur temporaire pour sauvegarder le volume
docker run --rm -v budget_postgres_data:/data -v ${PWD}/backups:/backup alpine tar czf /backup/postgres_volume_backup.tar.gz -C /data .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Volume sauvegardé: $volumeBackup" -ForegroundColor Green
} else {
    Write-Host "⚠️  Échec de la sauvegarde du volume, mais la sauvegarde SQL est OK" -ForegroundColor Yellow
}

# Étape 4: Résoudre le problème ContainerConfig
Write-Host "`n📋 ÉTAPE 4: Résolution du problème ContainerConfig" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Yellow

Write-Host "🗑️  Suppression du conteneur problématique (le volume est préservé)..." -ForegroundColor Yellow
docker rm -f budget_db 2>$null

Write-Host "🧹 Nettoyage des images orphelines..." -ForegroundColor Yellow
docker image prune -f

# Étape 5: Recréer le conteneur
Write-Host "`n📋 ÉTAPE 5: Recréation du conteneur" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Yellow

Write-Host "🚀 Recréation du conteneur db..." -ForegroundColor Green
docker-compose up -d db

# Attendre que le conteneur soit prêt
Write-Host "⏳ Attente du démarrage de PostgreSQL..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Vérifier que le conteneur fonctionne
$containerRunning = docker ps --filter "name=budget_db" --format "{{.Names}}"
if ($containerRunning) {
    Write-Host "✅ Conteneur db recréé avec succès!" -ForegroundColor Green
    
    # Vérifier que les données sont toujours là
    Write-Host "🔍 Vérification des données..." -ForegroundColor Yellow
    $tableCount = docker exec budget_db psql -U budget -d budget -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>$null
    
    if ($tableCount -and [int]$tableCount -gt 0) {
        Write-Host "✅ Les données sont présentes ($tableCount tables trouvées)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Aucune table trouvée. Vous devrez peut-être restaurer la sauvegarde." -ForegroundColor Yellow
        Write-Host "💡 Pour restaurer: .\scripts\restaurer-db.ps1 -BackupFile <fichier>" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Le conteneur n'a pas démarré correctement!" -ForegroundColor Red
    Write-Host "📋 Vérifiez les logs: docker-compose logs db" -ForegroundColor Yellow
    exit 1
}

# Étape 6: Redémarrer les autres services
Write-Host "`n📋 ÉTAPE 6: Redémarrage des autres services" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Yellow

Write-Host "🚀 Redémarrage des services..." -ForegroundColor Green
docker-compose up -d

Write-Host "`n✅ Procédure terminée!" -ForegroundColor Green
Write-Host "📊 Vérifiez que tout fonctionne: docker-compose ps" -ForegroundColor Yellow
Write-Host "📋 Voir les logs: docker-compose logs -f" -ForegroundColor Yellow
