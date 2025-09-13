# Installation Guide - Aya+ Backend

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Git

## 🚀 Installation Rapide

### 1. Cloner le projet
```bash
git clone <repository-url>
cd aya/aya_backend
```

### 2. Créer un environnement virtuel
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

#### Pour le développement :
```bash
pip install -r requirements-dev.txt
```

#### Pour la production :
```bash
pip install -r requirements-prod.txt
```

#### Pour les tests uniquement :
```bash
pip install -r requirements.txt
```

### 4. Configuration de l'environnement
```bash
# Copier le fichier d'exemple
cp env_example .env

# Éditer le fichier .env avec vos paramètres
```

### 5. Migrations de la base de données
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

### 7. Charger les données de test (optionnel)
```bash
python manage.py create_test_qr_codes
python create_test_vendors.py
```

### 8. Lancer le serveur
```bash
python manage.py runserver 0.0.0.0:8000
```

## 📦 Dépendances Principales

### Core Django
- **Django 5.2.6** : Framework web principal
- **djangorestframework 3.16.1** : API REST
- **djangorestframework-simplejwt 5.5.1** : Authentification JWT
- **django-cors-headers 4.8.0** : Gestion CORS

### Traitement d'images et QR Codes
- **Pillow 10.4.0** : Traitement d'images
- **qrcode[pil] 8.0** : Génération de QR codes

### Configuration
- **python-decouple 3.8** : Gestion des variables d'environnement

## 🔧 Dépendances de Développement

### Tests
- **pytest 7.4.3** : Framework de tests
- **pytest-django 4.7.0** : Intégration Django
- **coverage 7.3.2** : Couverture de code

### Qualité de code
- **black 23.11.0** : Formatage de code
- **flake8 6.1.0** : Linting
- **isort 5.12.0** : Tri des imports

### Debug
- **django-debug-toolbar 4.2.0** : Barre de debug
- **django-extensions 3.2.3** : Extensions Django

## 🚀 Dépendances de Production

### Serveur
- **gunicorn 21.2.0** : Serveur WSGI
- **whitenoise 6.6.0** : Servir les fichiers statiques

### Base de données
- **psycopg2-binary 2.9.9** : Driver PostgreSQL
- **redis 5.0.1** : Cache Redis
- **django-redis 5.4.0** : Intégration Django-Redis

### Sécurité
- **django-ratelimit 4.1.0** : Limitation de taux
- **django-axes 6.1.1** : Protection contre les attaques
- **django-csp 3.7** : Content Security Policy

### Monitoring
- **sentry-sdk[django] 1.38.0** : Monitoring d'erreurs

## 📱 Dépendances Flutter

Le projet Flutter utilise les dépendances suivantes (voir `pubspec.yaml`) :

### Core
- **mobile_scanner 3.5.6** : Scanner QR codes
- **shared_preferences 2.2.2** : Stockage local
- **http 1.1.0** : Requêtes HTTP
- **provider 6.1.1** : Gestion d'état

### UI & Animations
- **flutter_animate 4.2.0** : Animations
- **flutter_fortune_wheel 1.3.0** : Roue de la chance
- **scratcher 2.5.0** : Jeu de grattage

### QR Codes & PDF
- **qr_flutter 4.1.0** : Génération QR codes
- **pdf 3.10.7** : Génération PDF
- **printing 5.11.1** : Impression PDF

### Utilitaires
- **uuid 4.3.3** : Génération UUID
- **intl 0.19.0** : Internationalisation
- **url_launcher 6.2.4** : Ouverture d'URLs
- **share_plus 7.2.1** : Partage de fichiers

## 🔍 Vérification de l'installation

### Backend
```bash
# Vérifier que Django fonctionne
python manage.py check

# Lancer les tests
pytest

# Vérifier la couverture de code
coverage run -m pytest
coverage report
```

### Frontend Flutter
```bash
# Installer les dépendances
flutter pub get

# Vérifier la configuration
flutter doctor

# Lancer les tests
flutter test
```

## 🐛 Résolution de problèmes

### Erreur "PIL not found"
```bash
pip install Pillow
```

### Erreur "qrcode[pil] not found"
```bash
pip install qrcode[pil]
```

### Erreur de migration
```bash
python manage.py makemigrations --empty <app_name>
python manage.py migrate
```

### Erreur de permissions (Linux/Mac)
```bash
chmod +x manage.py
```

## 📚 Documentation

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Flutter Documentation](https://flutter.dev/docs)
- [QR Code Library](https://pypi.org/project/qrcode/)

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request
