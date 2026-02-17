# 🔧 Correction du Problème d'Authentification PostgreSQL

## Problème

Les logs PostgreSQL montrent :
```
FATAL: password authentication failed for user "budget"
```

Cela signifie que le mot de passe utilisé par Django ne correspond pas à celui configuré dans PostgreSQL.

## Solution

### Étape 1: Créer le fichier `.env`

Le `docker-compose.yml` utilise maintenant `.env` au lieu de `env.example`. Créez le fichier :

```powershell
# Copier env.example vers .env
Copy-Item env.example .env
```

### Étape 2: Vérifier les valeurs dans `.env`

Assurez-vous que `.env` contient :

```env
DB_NAME=budget
DB_USER=budget
DB_PASSWORD=P@ssw0rd7567542073340251
DB_HOST=db
DB_PORT=5432
```

### Étape 3: Redémarrer les services

```powershell
# Arrêter tous les services
docker-compose down -v

# Supprimer le volume PostgreSQL pour réinitialiser
docker volume rm budget_postgres_data

# Redémarrer
docker-compose up -d
```

### Étape 4: Vérifier la connexion

```powershell
# Voir les logs
docker-compose logs -f db

# Tester la connexion depuis le conteneur web
docker-compose exec web python manage.py migrate
```

## Alternative: Réinitialiser avec un mot de passe simple

Si vous préférez utiliser un mot de passe plus simple pour le développement :

1. Modifiez `.env` :
```env
DB_PASSWORD=budget
```

2. Modifiez `docker-compose.yml` ligne 9 :
```yaml
POSTGRES_PASSWORD: ${DB_PASSWORD:-budget}
```

3. Redémarrez :
```powershell
docker-compose down -v
docker volume rm budget_postgres_data
docker-compose up -d
```

## Vérification

Pour vérifier que tout fonctionne :

```powershell
# Vérifier les variables d'environnement dans le conteneur
docker-compose exec web env | grep DB_

# Devrait afficher :
# DB_NAME=budget
# DB_USER=budget
# DB_PASSWORD=P@ssw0rd7567542073340251
# DB_HOST=db
```

## Note Importante

⚠️ **Le fichier `.env` ne doit JAMAIS être commité dans Git !**

Il est déjà dans `.gitignore`, mais vérifiez qu'il n'est pas suivi :

```powershell
git status
```

Si `.env` apparaît, il est déjà dans Git et doit être supprimé de l'historique.
