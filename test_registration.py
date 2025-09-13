#!/usr/bin/env python
"""
Script de test pour l'API d'inscription
"""
import requests
import json

# URL de l'API
BASE_URL = "http://localhost:8000/api"

def test_registration():
    """Test de l'inscription d'un utilisateur"""
    
    # Données de test
    test_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "testpassword123",
        "password_confirm": "testpassword123"
    }
    
    print("🧪 Test d'inscription...")
    print(f"📤 Données envoyées: {json.dumps(test_data, indent=2)}")
    
    try:
        # Requête POST vers l'API d'inscription
        response = requests.post(
            f"{BASE_URL}/auth/register/",
            json=test_data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        
        print(f"📊 Statut de la réponse: {response.status_code}")
        print(f"📋 Headers de la réponse: {dict(response.headers)}")
        
        if response.status_code == 201:
            print("✅ Inscription réussie!")
            response_data = response.json()
            print(f"📄 Réponse: {json.dumps(response_data, indent=2)}")
        else:
            print("❌ Erreur d'inscription!")
            print(f"📄 Réponse: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erreur de connexion - Le serveur Django n'est pas démarré")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_cors():
    """Test de la configuration CORS"""
    print("\n🌐 Test de la configuration CORS...")
    
    try:
        # Test avec un header Origin
        response = requests.options(
            f"{BASE_URL}/auth/register/",
            headers={
                'Origin': 'http://10.0.2.2:8000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        )
        
        print(f"📊 Statut CORS: {response.status_code}")
        print(f"📋 Headers CORS: {dict(response.headers)}")
        
    except Exception as e:
        print(f"❌ Erreur CORS: {e}")

if __name__ == "__main__":
    test_cors()
    test_registration()
