#!/usr/bin/env python
"""
Test simple de l'API Django
"""
import requests
import json

def test_api():
    """Test simple de l'API"""
    try:
        # Test de l'endpoint d'inscription
        response = requests.post(
            "http://localhost:8000/api/auth/register/",
            json={
                "email": "test2@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password": "testpassword123",
                "password_confirm": "testpassword123"
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Inscription réussie!")
        else:
            print("❌ Erreur d'inscription")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_api()
