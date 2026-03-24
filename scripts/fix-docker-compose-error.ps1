# Script PowerShell pour résoudre l'erreur ContainerConfig de docker-compose

Write-Host "🔧 Résolution de l'erreur ContainerConfig..." -ForegroundColor Cyan

# 1. Arrêter tous les conteneurs
Write-Host "📦 Arrêt des conteneurs..." -ForegroundColor Yellow
docker-compose down

# 2. Supprimer le conteneur problématique
Write-Host "🗑️  Suppression du conteneur db..." -ForegroundColor Yellow
docker rm -f budget_db 2>$null

# 3. Nettoyer les images orphelines
Write-Host "🧹 Nettoyage des images..." -ForegroundColor Yellow
docker image prune -f

# 4. Demander confirmation pour supprimer le volume
$response = Read-Host "⚠️  Voulez-vous supprimer le volume PostgreSQL? Cela supprimera toutes les données. (y/N)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host "🗑️  Suppression du volume postgres_data..." -ForegroundColor Yellow
    docker volume rm budget_postgres_data 2>$null
}

# 5. Reconstruire et redémarrer
Write-Host "🚀 Reconstruction et redémarrage..." -ForegroundColor Green
docker-compose up -d --build

Write-Host "✅ Terminé! Vérifiez les logs avec: docker-compose logs -f db" -ForegroundColor Green
