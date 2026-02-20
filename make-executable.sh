#!/bin/bash
# Script pour rendre tous les scripts exécutables

echo "🔧 Rendre tous les scripts exécutables..."

# Rendre ce script lui-même exécutable
chmod +x "$0" 2>/dev/null || true

# Liste des scripts à rendre exécutables
SCRIPTS=(
    "install.sh"
    "setup-ssl.sh"
    "renew-ssl.sh"
    "fix-certbot-permissions.sh"
    "git-pull-safe.sh"
    "fix-docker-error.sh"
    "fix-ssl-challenge.sh"
    "configure-nginx.sh"
    "fix-django-allowed-hosts.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if chmod +x "$script" 2>/dev/null; then
            echo "✅ $script rendu exécutable"
        else
            echo "⚠️  Impossible de rendre $script exécutable (essayez avec sudo)"
            sudo chmod +x "$script" 2>/dev/null && echo "✅ $script rendu exécutable (avec sudo)" || echo "❌ Échec pour $script"
        fi
    else
        echo "⚠️  $script non trouvé"
    fi
done

echo ""
echo "✅ Tous les scripts sont maintenant exécutables!"
