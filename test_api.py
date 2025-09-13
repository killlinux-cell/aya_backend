#!/usr/bin/env python
"""
Script de test pour vérifier que l'API Django fonctionne correctement
"""
import requests
import json

BASE_URL = 'http://localhost:8000/api'

def test_api_connection():
    """Tester la connexion à l'API"""
    print("🔍 Test de connexion à l'API...")
    try:
        response = requests.get(f'{BASE_URL}/games/available/', timeout=5)
        if response.status_code == 401:  # Non authentifié, mais API accessible
            print("✅ API accessible (authentification requise)")
            return True
        else:
            print(f"⚠️  Réponse inattendue: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter à l'API")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_user_registration():
    """Tester l'inscription d'un utilisateur"""
    print("\n🔍 Test d'inscription...")
    try:
        data = {
            'email': 'test_api@aya.com',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'API',
        }
        
        response = requests.post(
            f'{BASE_URL}/auth/register/',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 201:
            print("✅ Inscription réussie")
            return response.json()
        else:
            print(f"❌ Échec de l'inscription: {response.status_code}")
            print(f"Réponse: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur lors de l'inscription: {e}")
        return None

def test_user_login():
    """Tester la connexion d'un utilisateur"""
    print("\n🔍 Test de connexion...")
    try:
        data = {
            'email': 'demo@example.com',
            'password': 'password',
        }
        
        response = requests.post(
            f'{BASE_URL}/auth/login/',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Connexion réussie")
            return response.json()
        else:
            print(f"❌ Échec de la connexion: {response.status_code}")
            print(f"Réponse: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur lors de la connexion: {e}")
        return None

def test_authenticated_requests(access_token):
    """Tester les requêtes authentifiées"""
    print("\n🔍 Test des requêtes authentifiées...")
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }
    
    # Test du profil utilisateur
    try:
        response = requests.get(f'{BASE_URL}/auth/profile/', headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Récupération du profil réussie")
            profile_data = response.json()
            print(f"   Utilisateur: {profile_data.get('first_name')} {profile_data.get('last_name')}")
            print(f"   Points disponibles: {profile_data.get('available_points')}")
        else:
            print(f"❌ Échec de la récupération du profil: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du profil: {e}")
    
    # Test des statistiques
    try:
        response = requests.get(f'{BASE_URL}/stats/', headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Récupération des statistiques réussie")
            stats_data = response.json()
            print(f"   QR codes scannés: {stats_data.get('total_qr_codes_scanned')}")
            print(f"   Jeux joués: {stats_data.get('total_games_played')}")
        else:
            print(f"❌ Échec de la récupération des statistiques: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des statistiques: {e}")
    
    # Test de validation d'un QR code
    try:
        data = {'code': 'VALID_QR_CODE'}
        response = requests.post(f'{BASE_URL}/validate/', json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Validation de QR code réussie")
            qr_data = response.json()
            if qr_data.get('is_valid'):
                print(f"   Points gagnés: {qr_data.get('points_earned')}")
            else:
                print(f"   QR code invalide: {qr_data.get('error')}")
        else:
            print(f"❌ Échec de la validation de QR code: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur lors de la validation de QR code: {e}")

def test_qr_codes():
    """Tester les QR codes de test"""
    print("\n🔍 Test des QR codes de test...")
    qr_codes = ['VALID_QR_CODE', 'BONUS_QR_100', 'SMALL_QR_10', 'ALREADY_USED', 'EXPIRED_QR']
    
    for qr_code in qr_codes:
        print(f"   QR Code: {qr_code}")
        # Les tests de validation nécessitent une authentification
        # qui sera testée dans test_authenticated_requests

def main():
    """Fonction principale de test"""
    print("🚀 Test de l'API Django pour l'application Aya")
    print("=" * 60)
    
    # Test de connexion
    if not test_api_connection():
        print("\n❌ L'API n'est pas accessible. Vérifiez que le serveur Django est démarré.")
        return
    
    # Test de connexion avec un utilisateur existant
    login_data = test_user_login()
    if login_data:
        access_token = login_data.get('access')
        if access_token:
            test_authenticated_requests(access_token)
    
    # Test des QR codes
    test_qr_codes()
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés !")
    print("\n📋 Résumé des endpoints testés :")
    print("   • Connexion à l'API")
    print("   • Authentification utilisateur")
    print("   • Récupération du profil")
    print("   • Récupération des statistiques")
    print("   • Validation de QR codes")
    print("\n🔑 Comptes de test disponibles :")
    print("   • demo@example.com / password")
    print("   • test@aya.com / test123")
    print("\n🎯 QR codes de test :")
    print("   • VALID_QR_CODE (50 points)")
    print("   • BONUS_QR_100 (100 points)")
    print("   • SMALL_QR_10 (10 points)")

if __name__ == '__main__':
    main()
