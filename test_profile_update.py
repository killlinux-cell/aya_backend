#!/usr/bin/env python3
"""
Test de mise à jour du profil utilisateur
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
AUTH_URL = f"{BASE_URL}/auth/"

# Données de test
test_user = {
    "email": "testuser2@test.com",
    "password": "finalpassword123"  # Mot de passe final
}

def test_login():
    """Test de connexion"""
    print("🔍 Test de connexion...")
    
    response = requests.post(f"{AUTH_URL}login/", json=test_user)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Connexion réussie!")
        return data['access']
    else:
        print("❌ Échec de la connexion")
        return None

def test_profile_update(access_token):
    """Test de mise à jour du profil"""
    print("\n🔍 Test de mise à jour du profil...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Mise à jour du nom
    update_data = {
        "first_name": "TestUpdated",
        "last_name": "UserUpdated"
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

def test_email_update(access_token):
    """Test de mise à jour de l'email"""
    print("\n🔍 Test de mise à jour de l'email...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Test 2: Mise à jour de l'email (avec tous les champs obligatoires)
    update_data = {
        "first_name": "TestUpdated",
        "last_name": "UserUpdated", 
        "email": "testuser2updated@test.com"
    }
    
    response = requests.put(f"{AUTH_URL}profile/update/", json=update_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Mise à jour de l'email réussie!")
        return True
    else:
        print("❌ Échec de la mise à jour de l'email")
        return False

def test_password_change(access_token):
    """Test de changement de mot de passe"""
    print("\n🔍 Test de changement de mot de passe...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    password_data = {
        "old_password": "finalpassword123",
        "new_password": "newfinalpassword123",
        "new_password_confirm": "newfinalpassword123"
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

def main():
    """Fonction principale de test"""
    print("🚀 TEST DE MISE À JOUR DU PROFIL")
    print("=" * 40)
    
    # Test de connexion
    access_token = test_login()
    if not access_token:
        print("❌ Impossible de continuer sans token d'accès")
        return
    
    # Test de mise à jour du profil
    profile_success = test_profile_update(access_token)
    
    # Test de mise à jour de l'email
    email_success = test_email_update(access_token)
    
    # Test de changement de mot de passe
    password_success = test_password_change(access_token)
    
    # Résumé
    print("\n" + "=" * 40)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 40)
    print(f"Mise à jour profil: {'✅' if profile_success else '❌'}")
    print(f"Mise à jour email: {'✅' if email_success else '❌'}")
    print(f"Changement mot de passe: {'✅' if password_success else '❌'}")
    
    total_tests = 3
    passed_tests = sum([profile_success, email_success, password_success])
    
    print(f"\n🎯 Résultat: {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
    else:
        print("⚠️ Certains tests ont échoué")

if __name__ == "__main__":
    main()
