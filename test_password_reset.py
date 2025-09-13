#!/usr/bin/env python3
"""
Test complet de la réinitialisation du mot de passe
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
AUTH_URL = f"{BASE_URL}/auth/"

def test_password_reset_request():
    """Test de demande de réinitialisation de mot de passe"""
    print("🔍 Test de demande de réinitialisation de mot de passe...")
    
    reset_data = {
        "email": "testuser2@test.com"
    }
    
    response = requests.post(f"{AUTH_URL}password/reset/request/", json=reset_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Demande de réinitialisation réussie!")
        print(f"Token généré: {data.get('token', 'N/A')}")
        return data.get('token')
    else:
        print("❌ Échec de la demande de réinitialisation")
        return None

def test_password_reset_confirm(token):
    """Test de confirmation de réinitialisation avec le token"""
    print("\n🔍 Test de confirmation de réinitialisation...")
    
    if not token:
        print("❌ Aucun token disponible pour le test")
        return False
    
    confirm_data = {
        "token": token,
        "new_password": "newresetpassword123",
        "new_password_confirm": "newresetpassword123"
    }
    
    response = requests.post(f"{AUTH_URL}password/reset/confirm/", json=confirm_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Confirmation de réinitialisation réussie!")
        return True
    else:
        print("❌ Échec de la confirmation de réinitialisation")
        return False

def test_login_with_new_password():
    """Test de connexion avec le nouveau mot de passe"""
    print("\n🔍 Test de connexion avec le nouveau mot de passe...")
    
    login_data = {
        "email": "testuser2@test.com",
        "password": "newresetpassword123"
    }
    
    response = requests.post(f"{AUTH_URL}login/", json=login_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Connexion avec le nouveau mot de passe réussie!")
        return True
    else:
        print("❌ Échec de la connexion avec le nouveau mot de passe")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 TEST COMPLET DE RÉINITIALISATION DU MOT DE PASSE")
    print("=" * 60)
    
    # Test 1: Demande de réinitialisation
    token = test_password_reset_request()
    
    # Test 2: Confirmation avec le token
    confirm_success = test_password_reset_confirm(token)
    
    # Test 3: Connexion avec le nouveau mot de passe
    login_success = test_login_with_new_password()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"Demande de réinitialisation: {'✅' if token else '❌'}")
    print(f"Confirmation avec token: {'✅' if confirm_success else '❌'}")
    print(f"Connexion avec nouveau mot de passe: {'✅' if login_success else '❌'}")
    
    total_tests = 3
    passed_tests = sum([bool(token), confirm_success, login_success])
    
    print(f"\n🎯 Résultat: {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("🎉 RÉINITIALISATION DU MOT DE PASSE FONCTIONNE!")
    else:
        print("⚠️ La réinitialisation du mot de passe a des problèmes")
        
        if not token:
            print("🔧 Problème: La demande de réinitialisation échoue")
        if not confirm_success:
            print("🔧 Problème: La confirmation avec le token échoue")
        if not login_success:
            print("🔧 Problème: La connexion avec le nouveau mot de passe échoue")

if __name__ == "__main__":
    main()
