# 🚀 Guide de Déploiement

Ce guide explique comment mettre à jour le conteneur web Django en production sans affecter la base de données.

## ⚠️ Important

- **La base de données ne sera PAS modifiée** lors du déploiement
- Seul le conteneur `web` (Django) sera mis à jour
- Les conteneurs `db` (PostgreSQL) et `redis` restent intacts

## 🚀 Déploiement Automatique (Recommandé)

### Méthode 1: Script de déploiement

```bash
# Rendre le script exécutable
chmod +x deploy-web.sh

# Lancer le déploiement
./deploy-web.sh
```

Le script va :
1. ✅ Sauvegarder vos modifications locales (optionnel)
2. ✅ Récupérer le nouveau code (git pull)
3. ✅ Vérifier que la base de données est intacte
4. ✅ Arrêter uniquement le conteneur web
5. ✅ Reconstruire l'image Docker du service web
6. ✅ Redémarrer le conteneur web
7. ✅ Appliquer les migrations (optionnel)
8. ✅ Collecter les fichiers statiques (optionnel)

## 📋 Déploiement Manuel

Si vous préférez faire le déploiement manuellement :

```bash
# 1. Récupérer le nouveau code
git pull

# 2. Arrêter uniquement le conteneur web
docker-compose stop web

# 3. Reconstruire l'image du service web
docker-compose build web

# 4. Redémarrer le conteneur web
docker-compose up -d web

# 5. Appliquer les migrations (si nécessaire)
docker-compose exec web python manage.py migrate

# 6. Collecter les fichiers statiques (si nécessaire)
docker-compose exec web python manage.py collectstatic --noinput
```

## 🔄 Déploiement Rapide (sans git pull)

Si vous avez déjà le code à jour localement :

```bash
# Arrêter et reconstruire
docker-compose stop web
docker-compose build web
docker-compose up -d web

# Vérifier les logs
docker-compose logs -f web
```

## 📊 Vérification après Déploiement

```bash
# Vérifier que le conteneur est démarré
docker-compose ps web

# Vérifier les logs
docker-compose logs web | tail -50

# Tester que Django répond
curl http://localhost:8000/

# Vérifier que la base de données est toujours accessible
docker-compose exec web python manage.py dbshell
```

## 🛠️ Commandes Utiles

### Voir les logs en temps réel
```bash
docker-compose logs -f web
```

### Redémarrer uniquement le conteneur web
```bash
docker-compose restart web
```

### Vérifier le statut de tous les services
```bash
docker-compose ps
```

### Accéder au shell du conteneur web
```bash
docker-compose exec web bash
```

### Appliquer les migrations manuellement
```bash
docker-compose exec web python manage.py migrate
```

### Collecter les fichiers statiques
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

## ⚠️ En Cas de Problème

### Le conteneur ne démarre pas

```bash
# Voir les logs d'erreur
docker-compose logs web

# Vérifier la configuration
docker-compose config

# Redémarrer depuis zéro
docker-compose down web
docker-compose up -d web
```

### Erreur de migration

```bash
# Voir les migrations en attente
docker-compose exec web python manage.py showmigrations

# Appliquer les migrations une par une
docker-compose exec web python manage.py migrate <app_name>
```

### Revenir à la version précédente

```bash
# Arrêter le conteneur
docker-compose stop web

# Utiliser git pour revenir en arrière
git checkout <commit-hash>

# Reconstruire et redémarrer
docker-compose build web
docker-compose up -d web
```

## 🔒 Sécurité

- ✅ Ne jamais supprimer les volumes de la base de données
- ✅ Toujours faire une sauvegarde avant un déploiement majeur
- ✅ Tester les migrations en local avant de les appliquer en production
- ✅ Vérifier les logs après chaque déploiement

## 📝 Notes

- Le script `deploy-web.sh` sauvegarde automatiquement vos modifications locales avec `git stash`
- Les migrations sont optionnelles et peuvent être appliquées manuellement
- La collecte des fichiers statiques est optionnelle (WhiteNoise peut servir les fichiers sans collectstatic)
