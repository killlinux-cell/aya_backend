#!/usr/bin/env python
import os
import django
import subprocess
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_superuser():
    """Créer un superutilisateur pour l'admin Django"""
    if not User.objects.filter(email='admin@aya.com').exists():
        User.objects.create_superuser(
            email='admin@aya.com',
            password='admin123',
            first_name='Admin',
            last_name='Aya'
        )
        print("✅ Superutilisateur créé avec succès !")
        print("📧 Email: admin@aya.com")
        print("🔑 Mot de passe: admin123")
    else:
        print("ℹ️  Le superutilisateur existe déjà.")

def start_server():
    """Démarrer le serveur Django"""
    print("🚀 Démarrage du serveur Django...")
    print("🌐 Admin Django: http://localhost:8000/admin/")
    print("📱 API: http://localhost:8000/api/")
    print("⏹️  Appuyez sur Ctrl+C pour arrêter le serveur")
    
    try:
        subprocess.run([sys.executable, 'manage.py', 'runserver'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Serveur arrêté.")

if __name__ == '__main__':
    print("🔧 Configuration de l'admin Django Aya...")
    create_superuser()
    print("\n" + "="*50)
    start_server()
