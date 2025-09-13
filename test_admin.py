#!/usr/bin/env python
import os
import django
import requests

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

def test_admin_access():
    """Tester l'accès à l'admin Django"""
    try:
        response = requests.get('http://localhost:8000/admin/', timeout=5)
        if response.status_code == 200:
            print("✅ Admin Django accessible : http://localhost:8000/admin/")
            print("📧 Email: admin@aya.com")
            print("🔑 Mot de passe: admin123")
            return True
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Impossible de se connecter à l'admin: {e}")
        return False

def test_api_access():
    """Tester l'accès à l'API"""
    try:
        response = requests.get('http://localhost:8000/api/games/available/', timeout=5)
        if response.status_code == 200:
            print("✅ API Django accessible : http://localhost:8000/api/")
            return True
        else:
            print(f"❌ Erreur API HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Impossible de se connecter à l'API: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Test de l'admin Django Aya...")
    print("="*50)
    
    admin_ok = test_admin_access()
    api_ok = test_api_access()
    
    print("="*50)
    if admin_ok and api_ok:
        print("🎉 Tous les tests sont passés !")
        print("🚀 L'application est prête à l'utilisation.")
    else:
        print("⚠️  Certains tests ont échoué.")
        print("💡 Vérifiez que le serveur Django est démarré.")
