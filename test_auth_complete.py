#!/usr/bin/env python3
"""
Test complet de toutes les fonctionnalités d'authentification
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
AUTH_URL = f"{BASE_URL}/auth/"

# Données de test
test_user = {
    "email": "testuser2@test.com",
    "password": "testpassword123"
}

def test_registration():
    """Test d'inscription d'un nouvel utilisateur"""
    print("🔍 Test d'inscription...")
    
    registration_data = {
        "email": "testuser2@test.com",
        "first_name": "Test",
        "last_name": "User2",
        "password": "testpassword123",
        "password_confirm": "testpassword123"
    }
    
    response = requests.post(f"{AUTH_URL}register/", json=registration_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 201:
        print("✅ Inscription réussie!")
        return True
    else:
        print("❌ Échec de l'inscription")
        return False

def test_login():
    """Test de connexion"""
    print("\n🔍 Test de connexion...")
    
    response = requests.post(f"{AUTH_URL}login/", json=test_user)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Connexion réussie!")
        print(f"User: {data['user']['email']}")
        print(f"Points: {data['user']['available_points']}")
        return data['access']
    else:
        print("❌ Échec de la connexion")
        return None

def test_profile_access(access_token):
    """Test d'accès au profil"""
    print("\n🔍 Test d'accès au profil...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{AUTH_URL}profile/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Accès au profil réussi!")
        return True
    else:
        print("❌ Échec de l'accès au profil")
        return False

def test_profile_update(access_token):
    """Test de mise à jour du profil"""
    print("\n🔍 Test de mise à jour du profil...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    update_data = {
        "first_name": "Updated",
        "last_name": "Name"
    }
    
    response = requests.put(f"{AUTH_URL}profile/update/", json=update_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Mise à jour du profil réussie!")
        return True
    else:
        print("❌ Échec de la mise à jour du profil")
        return False

def test_password_change(access_token):
    """Test de changement de mot de passe"""
    print("\n🔍 Test de changement de mot de passe...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    password_data = {
        "old_password": "testpassword123",
        "new_password": "newpassword123",
        "new_password_confirm": "newpassword123"
    }
    
    response = requests.post(f"{AUTH_URL}password/change/", json=password_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Changement de mot de passe réussi!")
        return True
    else:
        print("❌ Échec du changement de mot de passe")
        return False

def test_password_reset_request():
    """Test de demande de réinitialisation de mot de passe"""
    print("\n🔍 Test de demande de réinitialisation de mot de passe...")
    
    reset_data = {
        "email": "testuser2@test.com"
    }
    
    response = requests.post(f"{AUTH_URL}password/reset/request/", json=reset_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Demande de réinitialisation réussie!")
        return True
    else:
        print("❌ Échec de la demande de réinitialisation")
        return False

def test_user_stats(access_token):
    """Test des statistiques utilisateur"""
    print("\n🔍 Test des statistiques utilisateur...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{AUTH_URL}stats/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Statistiques récupérées avec succès!")
        return True
    else:
        print("❌ Échec de la récupération des statistiques")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 TEST COMPLET DE L'AUTHENTIFICATION")
    print("=" * 50)
    
    # Test d'inscription
    registration_success = test_registration()
    
    # Test de connexion
    access_token = test_login()
    if not access_token:
        print("❌ Impossible de continuer sans token d'accès")
        return
    
    # Test d'accès au profil
    profile_success = test_profile_access(access_token)
    
    # Test de mise à jour du profil
    update_success = test_profile_update(access_token)
    
    # Test de changement de mot de passe
    password_success = test_password_change(access_token)
    
    # Test de demande de réinitialisation
    reset_success = test_password_reset_request()
    
    # Test des statistiques
    stats_success = test_user_stats(access_token)
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    print(f"Inscription: {'✅' if registration_success else '❌'}")
    print(f"Connexion: {'✅' if access_token else '❌'}")
    print(f"Profil: {'✅' if profile_success else '❌'}")
    print(f"Mise à jour profil: {'✅' if update_success else '❌'}")
    print(f"Changement mot de passe: {'✅' if password_success else '❌'}")
    print(f"Réinitialisation: {'✅' if reset_success else '❌'}")
    print(f"Statistiques: {'✅' if stats_success else '❌'}")
    
    total_tests = 7
    passed_tests = sum([
        registration_success,
        bool(access_token),
        profile_success,
        update_success,
        password_success,
        reset_success,
        stats_success
    ])
    
    print(f"\n🎯 Résultat: {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
    else:
        print("⚠️ Certains tests ont échoué")

if __name__ == "__main__":
    main()
