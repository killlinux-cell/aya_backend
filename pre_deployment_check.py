#!/usr/bin/env python
"""
Script de vérification pré-déploiement pour Aya Backend
Exécutez ce script avant de mettre en ligne : python pre_deployment_check.py
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
import subprocess

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def check_debug():
    """Vérifier que DEBUG est False"""
    print("\n" + Colors.BOLD + "🔒 Vérification DEBUG" + Colors.END)
    if settings.DEBUG:
        print_error("DEBUG est activé (True). Désactivez-le en production !")
        return False
    else:
        print_success("DEBUG est désactivé")
        return True

def check_secret_key():
    """Vérifier que SECRET_KEY n'est pas la valeur par défaut"""
    print("\n" + Colors.BOLD + "🔑 Vérification SECRET_KEY" + Colors.END)
    default_key = 'django-insecure-(xiy56oj+q9vlkvn0m-2ade0my=d!j4s*pqt50wh9#n$o9d&6w'
    if settings.SECRET_KEY == default_key:
        print_error("SECRET_KEY utilise la valeur par défaut. Changez-la !")
        return False
    elif len(settings.SECRET_KEY) < 50:
        print_warning("SECRET_KEY semble trop courte")
        return False
    else:
        print_success("SECRET_KEY est configurée")
        return True

def check_allowed_hosts():
    """Vérifier ALLOWED_HOSTS"""
    print("\n" + Colors.BOLD + "🌐 Vérification ALLOWED_HOSTS" + Colors.END)
    if '*' in settings.ALLOWED_HOSTS:
        print_error("ALLOWED_HOSTS contient '*'. C'est dangereux en production !")
        return False
    elif not settings.ALLOWED_HOSTS:
        print_error("ALLOWED_HOSTS est vide")
        return False
    else:
        print_success(f"ALLOWED_HOSTS configuré : {', '.join(settings.ALLOWED_HOSTS)}")
        return True

def check_static_files():
    """Vérifier la configuration des fichiers statiques"""
    print("\n" + Colors.BOLD + "📁 Vérification Static Files" + Colors.END)
    if not settings.STATIC_ROOT:
        print_warning("STATIC_ROOT n'est pas configuré")
        return False
    else:
        print_success(f"STATIC_ROOT : {settings.STATIC_ROOT}")
        return True

def check_media_files():
    """Vérifier la configuration des fichiers media"""
    print("\n" + Colors.BOLD + "📁 Vérification Media Files" + Colors.END)
    if not settings.MEDIA_ROOT:
        print_warning("MEDIA_ROOT n'est pas configuré")
        return False
    else:
        media_path = Path(settings.MEDIA_ROOT)
        if not media_path.exists():
            print_warning(f"Le dossier MEDIA_ROOT n'existe pas : {media_path}")
            try:
                media_path.mkdir(parents=True, exist_ok=True)
                print_success(f"Dossier créé : {media_path}")
            except Exception as e:
                print_error(f"Impossible de créer le dossier : {e}")
                return False
        print_success(f"MEDIA_ROOT : {settings.MEDIA_ROOT}")
        return True

def check_database():
    """Vérifier la connexion à la base de données"""
    print("\n" + Colors.BOLD + "🗄️  Vérification Base de Données" + Colors.END)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print_success("Connexion à la base de données OK")
        return True
    except Exception as e:
        print_error(f"Erreur de connexion à la base de données : {e}")
        return False

def check_migrations():
    """Vérifier les migrations"""
    print("\n" + Colors.BOLD + "🔄 Vérification Migrations" + Colors.END)
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'showmigrations', '--plan'],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        if '[ ]' in result.stdout:
            print_warning("Il y a des migrations non appliquées")
            print_info("Exécutez : python manage.py migrate")
            return False
        else:
            print_success("Toutes les migrations sont appliquées")
            return True
    except Exception as e:
        print_error(f"Erreur lors de la vérification des migrations : {e}")
        return False

def check_django_check():
    """Exécuter django check"""
    print("\n" + Colors.BOLD + "🧪 Exécution de django check" + Colors.END)
    try:
        call_command('check')
        print_success("Django check : Aucune erreur")
        return True
    except CommandError as e:
        print_error(f"Django check a trouvé des erreurs : {e}")
        return False

def check_django_check_deploy():
    """Exécuter django check --deploy"""
    print("\n" + Colors.BOLD + "🚀 Exécution de django check --deploy" + Colors.END)
    try:
        call_command('check', '--deploy')
        print_success("Django check --deploy : Aucune erreur")
        return True
    except CommandError as e:
        print_error(f"Django check --deploy a trouvé des problèmes : {e}")
        return False

def check_env_file():
    """Vérifier la présence du fichier .env"""
    print("\n" + Colors.BOLD + "📄 Vérification fichier .env" + Colors.END)
    env_file = BASE_DIR / '.env'
    if not env_file.exists():
        print_warning("Le fichier .env n'existe pas")
        print_info("Créez un fichier .env basé sur env_example")
        return False
    else:
        print_success("Fichier .env trouvé")
        # Vérifier qu'il contient les variables essentielles
        with open(env_file, 'r') as f:
            content = f.read()
            required_vars = ['SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS']
            missing = [var for var in required_vars if var not in content]
            if missing:
                print_warning(f"Variables manquantes dans .env : {', '.join(missing)}")
                return False
        return True

def check_https_settings():
    """Vérifier les paramètres HTTPS"""
    print("\n" + Colors.BOLD + "🔐 Vérification Paramètres HTTPS" + Colors.END)
    issues = []
    if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
        issues.append("SECURE_SSL_REDIRECT devrait être True en production")
    if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
        issues.append("SESSION_COOKIE_SECURE devrait être True en production")
    if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
        issues.append("CSRF_COOKIE_SECURE devrait être True en production")
    
    if issues:
        for issue in issues:
            print_warning(issue)
        return False
    else:
        print_success("Paramètres HTTPS configurés")
        return True

def main():
    """Fonction principale"""
    # Configurer l'encodage UTF-8 pour Windows
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print(Colors.BOLD + "\n" + "="*60)
    print("VERIFICATION PRE-DEPLOIEMENT AYA BACKEND")
    print("="*60 + Colors.END)
    
    results = []
    
    # Vérifications critiques
    results.append(("DEBUG", check_debug()))
    results.append(("SECRET_KEY", check_secret_key()))
    results.append(("ALLOWED_HOSTS", check_allowed_hosts()))
    results.append(("Base de données", check_database()))
    results.append(("Migrations", check_migrations()))
    results.append(("Django check", check_django_check()))
    
    # Vérifications importantes
    results.append(("Static files", check_static_files()))
    results.append(("Media files", check_media_files()))
    results.append(("Fichier .env", check_env_file()))
    
    # Vérifications optionnelles (avertissements)
    results.append(("HTTPS settings", check_https_settings()))
    
    # Résumé
    print("\n" + Colors.BOLD + "="*60)
    print("📊 RÉSUMÉ")
    print("="*60 + Colors.END)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ OK" if result else "❌ ÉCHEC"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.END} - {name}")
    
    print(f"\n{Colors.BOLD}Résultat : {passed}/{total} vérifications réussies{Colors.END}")
    
    if passed == total:
        print_success("\n🎉 Toutes les vérifications sont passées ! Vous pouvez déployer.")
        return 0
    else:
        print_error(f"\n⚠️  {total - passed} vérification(s) ont échoué. Corrigez les problèmes avant de déployer.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

