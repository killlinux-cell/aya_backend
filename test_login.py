#!/usr/bin/env python
"""
Test de connexion avec un utilisateur existant
"""
import requests
import json

def test_login():
    """Test de connexion"""
    try:
        # Test de connexion avec l'utilisateur créé précédemment
        response = requests.post(
            "http://localhost:8000/api/auth/login/",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Connexion réussie!")
            data = response.json()
            print(f"Access Token: {data.get('access', 'N/A')[:20]}...")
            print(f"User: {data.get('user', {}).get('email', 'N/A')}")
        else:
            print("❌ Erreur de connexion")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_login()
