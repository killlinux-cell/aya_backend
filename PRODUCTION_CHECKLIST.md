# ✅ Checklist de Vérification Pré-Production

## 🔒 Sécurité (CRITIQUE)

### Configuration Django
- [ ] `DEBUG = False` dans `.env` ou `settings.py`
- [ ] `SECRET_KEY` unique et sécurisé (pas la valeur par défaut)
- [ ] `ALLOWED_HOSTS` configuré avec les domaines réels (pas `*`)
- [ ] Variables sensibles (SECRET_KEY, passwords) dans `.env` (pas dans le code)
- [ ] HTTPS activé : `SECURE_SSL_REDIRECT = True`
- [ ] Cookies sécurisés : `SESSION_COOKIE_SECURE = True` et `CSRF_COOKIE_SECURE = True`

### Email
- [ ] Identifiants email dans `.env` (pas en clair dans le code)
- [ ] Test d'envoi d'email fonctionnel

## 📁 Fichiers et Chemins

### Static Files
- [ ] `STATIC_ROOT` configuré correctement pour le serveur
- [ ] `python manage.py collectstatic` exécuté
- [ ] Vérifier que les fichiers statiques sont servis correctement

### Media Files
- [ ] `MEDIA_ROOT` configuré correctement
- [ ] Permissions d'écriture sur le dossier `media/`
- [ ] Vérifier que les fichiers media sont accessibles

## 🗄️ Base de Données

- [ ] Migrations à jour : `python manage.py makemigrations`
- [ ] Migrations appliquées : `python manage.py migrate`
- [ ] Aucune migration en attente : `python manage.py showmigrations`
- [ ] Backup de la base de données effectué
- [ ] Si PostgreSQL/MySQL : connexion testée

## 🔗 URLs et Routes

- [ ] Toutes les URLs fonctionnent (`/api/auth/`, `/api/`, `/dashboard/`)
- [ ] Routes API testées
- [ ] Routes dashboard testées
- [ ] Pas d'erreurs 404 sur les routes principales

## 📦 Dépendances

- [ ] `requirements.txt` à jour
- [ ] Toutes les dépendances installées : `pip install -r requirements.txt`
- [ ] Pas de conflits de versions

## 🧪 Tests

- [ ] `python manage.py check` - Aucune erreur
- [ ] `python manage.py check --deploy` - Vérifications de déploiement
- [ ] Test de connexion API
- [ ] Test d'authentification
- [ ] Test des fonctionnalités principales

## 🌐 Configuration Serveur

### CORS
- [ ] `CORS_ALLOWED_ORIGINS` configuré (pas `CORS_ALLOW_ALL_ORIGINS = True`)
- [ ] Domaines Flutter ajoutés si nécessaire

### Serveur Web
- [ ] Gunicorn/uWSGI configuré (si applicable)
- [ ] Nginx configuré (si applicable)
- [ ] Ports ouverts (80, 443, 8000 si nécessaire)

## 📱 Application Flutter

- [ ] `DjangoConfig.baseUrl` pointe vers l'URL de production
- [ ] Certificats SSL valides
- [ ] Deep linking configuré
- [ ] Test sur appareil réel

## 📊 Monitoring

- [ ] Logs configurés
- [ ] Système de monitoring en place (optionnel)
- [ ] Alertes configurées (optionnel)

## 🔄 Scripts de Déploiement

- [ ] Script de déploiement testé
- [ ] Rollback planifié en cas de problème

## ✅ Checklist Finale

Avant de mettre en ligne, exécutez :

```bash
# 1. Vérifications Django
python manage.py check
python manage.py check --deploy

# 2. Migrations
python manage.py showmigrations

# 3. Collectstatic (si nécessaire)
python manage.py collectstatic --noinput

# 4. Test serveur local
python manage.py runserver 0.0.0.0:8000
```

## 🚨 Points d'Attention

1. **NE JAMAIS** commiter le fichier `.env` avec des secrets
2. **TOUJOURS** utiliser `DEBUG = False` en production
3. **VÉRIFIER** que `ALLOWED_HOSTS` ne contient pas `*`
4. **TESTER** toutes les fonctionnalités avant la mise en ligne
5. **SAUVEGARDER** la base de données avant toute migration

