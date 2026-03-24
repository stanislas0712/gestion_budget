#!/bin/bash
# Script de renouvellement automatique des certificats SSL Let's Encrypt
# Nginx et Certbot doivent être installés localement sur le serveur Ubuntu

set +e  # Ne pas arrêter sur toutes les erreurs

echo "🔄 Renouvellement des certificats SSL..."

# Vérifier que Certbot est installé
if ! command -v certbot &> /dev/null; then
    echo "❌ Certbot n'est pas installé"
    echo "   Installez avec: sudo apt install -y certbot python3-certbot-nginx"
    exit 1
fi

# Renouveler les certificats avec Certbot local
echo "🔐 Renouvellement des certificats..."
if sudo certbot renew --quiet; then
    echo "✅ Certificats renouvelés avec succès"
    
    # Redémarrer Nginx pour charger les nouveaux certificats
    if sudo systemctl is-active --quiet nginx; then
        echo "🔄 Redémarrage de Nginx..."
        sudo systemctl reload nginx || sudo systemctl restart nginx
        echo "✅ Nginx redémarré avec les nouveaux certificats"
    else
        echo "⚠️  Nginx n'est pas en cours d'exécution"
    fi
else
    echo "⚠️  Aucun certificat à renouveler ou erreur lors du renouvellement"
fi

echo "✅ Renouvellement terminé"
