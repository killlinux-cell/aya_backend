# 🚀 Guide de Déploiement en Production

## 📋 Prérequis

1. Serveur avec Python 3.12+
2. Accès SSH au serveur
3. Domaine configuré (ex: `aya-plus.orapide.shop`)
4. Certificat SSL (Let's Encrypt recommandé)

## 🔧 Étape 1 : Préparation du Code

### 1.1 Vérifications Locales

```bash
# Exécuter le script de vérification
cd aya_backend
python pre_deployment_check.py

# Vérifier les migrations
python manage.py showmigrations

# Vérifier la configuration Django
python manage.py check
python manage.py check --deploy
```

### 1.2 Créer le fichier .env

```bash
# Copier le fichier exemple
cp env_example .env

# Éditer .env avec vos valeurs réelles
nano .env  # ou votre éditeur préféré
```

**Variables obligatoires dans .env :**
```env
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
DEBUG=False
ALLOWED_HOSTS=aya-plus.orapide.shop,199.231.191.234

# Email (si nécessaire)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-application
DEFAULT_FROM_EMAIL=votre-email@gmail.com
```

**⚠️ IMPORTANT :** Ne commitez JAMAIS le fichier `.env` !

## 📦 Étape 2 : Déploiement sur le Serveur

### 2.1 Transfert des Fichiers

```bash
# Option 1 : Via Git (recommandé)
git clone https://votre-repo.git
cd aya_backend

# Option 2 : Via SCP
scp -r aya_backend/ user@server:/var/www/
```

### 2.2 Installation des Dépendances

```bash
cd /var/www/aya_backend

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2.3 Configuration

```bash
# Créer le fichier .env
cp env_example .env
nano .env  # Configurer avec les valeurs de production

# Créer les dossiers nécessaires
mkdir -p media staticfiles
chmod 755 media staticfiles
```

### 2.4 Base de Données

```bash
# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur (si nécessaire)
python manage.py createsuperuser
```

### 2.5 Fichiers Statiques

```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

## 🌐 Étape 3 : Configuration du Serveur Web

### 3.1 Gunicorn (Optionnel mais recommandé)

```bash
# Installer Gunicorn
pip install gunicorn

# Tester Gunicorn
gunicorn aya_project.wsgi:application --bind 0.0.0.0:8000
```

### 3.2 Nginx (Recommandé)

Créer `/etc/nginx/sites-available/aya_backend` :

```nginx
server {
    listen 80;
    server_name aya-plus.orapide.shop;
    
    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aya-plus.orapide.shop;

    ssl_certificate /etc/letsencrypt/live/aya-plus.orapide.shop/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aya-plus.orapide.shop/privkey.pem;

    # Fichiers statiques
    location /static/ {
        alias /var/www/aya_backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Fichiers media
    location /media/ {
        alias /var/www/aya_backend/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Proxy vers Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activer le site :
```bash
sudo ln -s /etc/nginx/sites-available/aya_backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3.3 Certificat SSL (Let's Encrypt)

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir un certificat
sudo certbot --nginx -d aya-plus.orapide.shop

# Renouvellement automatique
sudo certbot renew --dry-run
```

## 🔄 Étape 4 : Service Systemd (Recommandé)

Créer `/etc/systemd/system/aya_backend.service` :

```ini
[Unit]
Description=Aya Backend Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/aya_backend
ExecStart=/var/www/aya_backend/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/aya_backend/aya_backend.sock \
    aya_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

Activer le service :
```bash
sudo systemctl daemon-reload
sudo systemctl enable aya_backend
sudo systemctl start aya_backend
sudo systemctl status aya_backend
```

## ✅ Étape 5 : Vérifications Finales

### 5.1 Tests

```bash
# Vérifier que le service fonctionne
sudo systemctl status aya_backend

# Vérifier les logs
sudo journalctl -u aya_backend -f

# Tester l'API
curl https://aya-plus.orapide.shop/api/auth/login/
```

### 5.2 Checklist

- [ ] Site accessible via HTTPS
- [ ] API fonctionnelle
- [ ] Dashboard accessible
- [ ] Fichiers statiques servis
- [ ] Fichiers media accessibles
- [ ] Emails fonctionnels (si configurés)
- [ ] Base de données opérationnelle

## 🔧 Maintenance

### Mises à Jour

```bash
# 1. Sauvegarder la base de données
python manage.py dumpdata > backup_$(date +%Y%m%d).json

# 2. Mettre à jour le code
git pull

# 3. Installer les nouvelles dépendances
pip install -r requirements.txt

# 4. Appliquer les migrations
python manage.py migrate

# 5. Collecter les nouveaux fichiers statiques
python manage.py collectstatic --noinput

# 6. Redémarrer le service
sudo systemctl restart aya_backend
```

### Logs

```bash
# Logs du service
sudo journalctl -u aya_backend -f

# Logs Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## 🚨 Dépannage

### Problème : 502 Bad Gateway

**Solution :**
```bash
# Vérifier que Gunicorn fonctionne
sudo systemctl status aya_backend

# Vérifier les permissions du socket
ls -la /var/www/aya_backend/aya_backend.sock
```

### Problème : Fichiers statiques non servis

**Solution :**
```bash
# Vérifier STATIC_ROOT
python manage.py shell
>>> from django.conf import settings
>>> print(settings.STATIC_ROOT)

# Recollecter les fichiers
python manage.py collectstatic --noinput
```

### Problème : Erreurs de permissions

**Solution :**
```bash
# Corriger les permissions
sudo chown -R www-data:www-data /var/www/aya_backend
sudo chmod -R 755 /var/www/aya_backend
```

## 📱 Configuration Flutter

Mettre à jour `lib/config/django_config.dart` :

```dart
static const String baseUrl = 'https://aya-plus.orapide.shop';
```

## 🔐 Sécurité

1. **Ne jamais** commiter `.env`
2. **Toujours** utiliser `DEBUG=False` en production
3. **Vérifier** régulièrement les mises à jour de sécurité
4. **Sauvegarder** régulièrement la base de données
5. **Monitorer** les logs pour détecter les intrusions

## 📞 Support

En cas de problème :
1. Vérifier les logs
2. Exécuter `python manage.py check`
3. Vérifier la configuration Nginx
4. Vérifier les permissions des fichiers

