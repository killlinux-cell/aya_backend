#!/usr/bin/env python
"""
Script pour démarrer le serveur Django avec l'admin
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

def main():
    """Démarrer le serveur Django"""
    print("🚀 Démarrage du serveur Django Admin...")
    print("=" * 50)
    print("📋 Informations :")
    print("• URL Admin : http://localhost:8000/admin/")
    print("• API : http://localhost:8000/api/")
    print("• Arrêter : Ctrl+C")
    print("=" * 50)
    
    try:
        # Démarrer le serveur de développement
        execute_from_command_line([
            'manage.py', 
            'runserver', 
            '0.0.0.0:8000',
            '--settings=aya_project.settings'
        ])
    except KeyboardInterrupt:
        print("\n👋 Serveur arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage : {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
