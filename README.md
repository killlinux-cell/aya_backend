# 🚀 Backend Django pour l'Application Aya

Backend complet avec authentification JWT, gestion des QR codes, jeux et échanges de points.

## 📋 Fonctionnalités

### 🔐 Authentification
- **Inscription** : Création de compte utilisateur
- **Connexion** : Authentification avec JWT
- **Profil** : Gestion du profil utilisateur
- **Mot de passe** : Changement et réinitialisation

### 🎯 QR Codes
- **Validation** : Scanner et valider des QR codes
- **Points** : Attribution automatique de points
- **Historique** : Suivi des QR codes scannés

### 🎮 Jeux
- **Scratch & Win** : Jeu de grattage
- **Roue de la Chance** : Jeu de roulette
- **Limites** : Un jeu par jour par type
- **Historique** : Suivi des parties jouées

### 💰 Échanges
- **Demandes** : Création de demandes d'échange
- **Validation** : Validation par les vendeurs
- **Historique** : Suivi des échanges

## 🛠️ Installation

### Prérequis
- Python 3.8+
- pip

### Installation
```bash
# Cloner le projet
cd aya_backend

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Créer les données de test
python create_test_data.py

# Lancer le serveur
python manage.py runserver
```

## 🌐 API Endpoints

### Authentification (`/api/auth/`)
- `POST /register/` - Inscription
- `POST /login/` - Connexion
- `POST /token/refresh/` - Rafraîchir le token
- `POST /logout/` - Déconnexion
- `GET /profile/` - Profil utilisateur
- `PUT /profile/update/` - Mettre à jour le profil
- `GET /stats/` - Statistiques utilisateur
- `POST /password/change/` - Changer le mot de passe
- `POST /password/reset/request/` - Demander une réinitialisation
- `POST /password/reset/confirm/` - Confirmer la réinitialisation

### QR Codes et Jeux (`/api/`)
- `POST /validate/` - Valider un QR code
- `GET /user-codes/` - QR codes scannés par l'utilisateur
- `POST /games/play/` - Jouer à un jeu
- `GET /games/history/` - Historique des jeux
- `GET /games/available/` - Jeux disponibles
- `POST /exchanges/create/` - Créer une demande d'échange
- `GET /exchanges/list/` - Liste des échanges
- `POST /exchanges/validate/` - Valider un code d'échange
- `POST /exchanges/confirm/` - Confirmer un échange
- `GET /stats/` - Statistiques détaillées

## 🔑 Comptes de Test

### Utilisateur de Démonstration
- **Email** : `demo@example.com`
- **Mot de passe** : `password`
- **Points disponibles** : 100
- **QR codes scannés** : 2

### Utilisateur Test
- **Email** : `test@aya.com`
- **Mot de passe** : `test123`
- **Points disponibles** : 200

## 🎯 QR Codes de Test

- `VALID_QR_CODE` - 50 points
- `BONUS_QR_100` - 100 points
- `SMALL_QR_10` - 10 points
- `ALREADY_USED` - 30 points (déjà utilisé)
- `EXPIRED_QR` - 25 points (expiré)

## 💱 Codes d'Échange de Test

- `EXCH_DEMO_001` - 30 points (complété)
- `EXCH_DEMO_002` - 20 points (en attente)

## 📱 Configuration Flutter

Pour connecter votre application Flutter à ce backend :

1. **URL de base** : `http://localhost:8000/api/`
2. **Authentification** : JWT Bearer Token
3. **Headers requis** :
   ```dart
   'Content-Type': 'application/json',
   'Authorization': 'Bearer $accessToken'
   ```

## 🔧 Configuration

### Variables d'environnement
Créer un fichier `.env` basé sur `env_example` :
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,10.0.2.2
DATABASE_URL=sqlite:///db.sqlite3
```

### CORS
Le backend est configuré pour accepter les requêtes depuis :
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:8080`
- `http://127.0.0.1:8080`

## 📊 Base de Données

### Modèles Principaux
- **User** : Utilisateur personnalisé avec points et QR code personnel
- **QRCode** : QR codes du système avec points et expiration
- **UserQRCode** : Association utilisateur-QR code scanné
- **GameHistory** : Historique des jeux joués
- **ExchangeRequest** : Demandes d'échange de points
- **DailyGameLimit** : Limites quotidiennes de jeux

## 🚀 Déploiement

### Production
1. Changer `DEBUG=False` dans les settings
2. Configurer une base de données PostgreSQL/MySQL
3. Configurer les variables d'environnement
4. Utiliser un serveur WSGI (Gunicorn)
5. Configurer un reverse proxy (Nginx)

### Docker (optionnel)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 📝 Logs et Debug

### Logs Django
```bash
# Activer les logs détaillés
python manage.py runserver --verbosity=2
```

### Admin Django
Accéder à l'interface d'administration :
- URL : `http://localhost:8000/admin/`
- Compte : `admin@aya.com` / `admin`

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commit les changements
4. Push vers la branche
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.

## 🆘 Support

Pour toute question ou problème :
1. Vérifier les logs Django
2. Tester les endpoints avec Postman/curl
3. Vérifier la configuration CORS
4. Consulter la documentation Django REST Framework
