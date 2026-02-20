# 🔧 Résolution des Conflits Git Pull

## Problème

Lors d'un `git pull`, vous obtenez :
```
error: Your local changes to the following files would be overwritten by merge:
        setup-ssl.sh
Please commit your changes or stash them before you merge.
```

## Solutions

### Solution 1: Sauvegarder vos modifications locales (Recommandé)

Si vous avez fait des modifications importantes que vous voulez garder :

```bash
# 1. Voir les différences
git diff setup-ssl.sh

# 2. Sauvegarder vos modifications
git stash

# 3. Faire le pull
git pull

# 4. Récupérer vos modifications
git stash pop

# 5. Résoudre les conflits si nécessaire
# Éditez le fichier pour fusionner les changements
```

### Solution 2: Commiter vos modifications

Si vos modifications locales sont finales :

```bash
# 1. Ajouter les fichiers modifiés
git add setup-ssl.sh

# 2. Commiter
git commit -m "Mise à jour setup-ssl.sh"

# 3. Faire le pull (peut nécessiter un merge)
git pull

# 4. Si conflit, résoudre puis :
git add setup-ssl.sh
git commit -m "Résolution conflit setup-ssl.sh"
```

### Solution 3: Écraser les modifications locales (Attention!)

Si vous voulez simplement utiliser la version distante :

```bash
# 1. Sauvegarder la version locale (au cas où)
cp setup-ssl.sh setup-ssl.sh.backup

# 2. Restaurer la version distante
git checkout -- setup-ssl.sh

# 3. Faire le pull
git pull
```

### Solution 4: Forcer l'utilisation de la version distante

```bash
# 1. Réinitialiser le fichier
git reset --hard origin/main

# 2. Faire le pull
git pull
```

## Script Automatique

Créez un script `git-pull-safe.sh` :

```bash
#!/bin/bash
# Script pour faire un pull en sécurité

echo "🔄 Vérification des modifications locales..."

# Vérifier s'il y a des modifications
if git diff --quiet && git diff --cached --quiet; then
    echo "✅ Aucune modification locale, pull direct..."
    git pull
else
    echo "⚠️  Modifications locales détectées"
    echo ""
    echo "Options:"
    echo "1. Stash les modifications puis pull"
    echo "2. Commiter les modifications puis pull"
    echo "3. Écraser les modifications locales"
    echo "4. Annuler"
    read -p "Choix (1-4): " choice
    
    case $choice in
        1)
            git stash
            git pull
            git stash pop
            echo "✅ Pull terminé, modifications récupérées"
            ;;
        2)
            git add .
            read -p "Message de commit: " msg
            git commit -m "$msg"
            git pull
            ;;
        3)
            git reset --hard origin/main
            git pull
            echo "✅ Pull terminé, modifications locales écrasées"
            ;;
        4)
            echo "❌ Opération annulée"
            exit 1
            ;;
        *)
            echo "❌ Choix invalide"
            exit 1
            ;;
    esac
fi
```

## Commandes Rapides

```bash
# Voir les fichiers modifiés
git status

# Voir les différences
git diff

# Stash + Pull + Pop (solution rapide)
git stash && git pull && git stash pop

# Forcer la version distante (si vous êtes sûr)
git reset --hard origin/main && git pull
```
