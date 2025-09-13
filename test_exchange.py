#!/usr/bin/env python3
"""
Test script pour vérifier les endpoints d'échange
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
LOGIN_URL = f"{BASE_URL}/auth/login/"
EXCHANGE_CREATE_URL = f"{BASE_URL}/exchanges/create/"

# Données de test
login_data = {
    "email": "test@example.com",
    "password": "test123"
}

def test_exchange_creation():
    """Test de création d'une demande d'échange"""
    print("🔍 Test de création d'une demande d'échange...")
    
    # 1. Se connecter
    print("1. Connexion...")
    login_response = requests.post(LOGIN_URL, json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Erreur de connexion: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    login_data_response = login_response.json()
    access_token = login_data_response['access']
    user_data = login_data_response['user']
    
    print(f"✅ Connexion réussie!")
    print(f"User: {user_data['email']}")
    print(f"Points disponibles: {user_data['available_points']}")
    
    # Vérifier si l'utilisateur a assez de points
    if user_data['available_points'] < 50:
        print(f"⚠️ L'utilisateur n'a que {user_data['available_points']} points, pas assez pour échanger 50 points")
        print("Test d'échange avec 10 points à la place...")
        exchange_points = 10
    else:
        exchange_points = 50
    
    # 2. Créer une demande d'échange
    print("\n2. Création d'une demande d'échange...")
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    exchange_data = {
        "points": exchange_points
    }
    
    exchange_response = requests.post(
        EXCHANGE_CREATE_URL, 
        json=exchange_data, 
        headers=headers
    )
    
    print(f"Status: {exchange_response.status_code}")
    print(f"Response: {exchange_response.text}")
    
    if exchange_response.status_code == 201:
        exchange_data_response = exchange_response.json()
        print(f"✅ Demande d'échange créée avec succès!")
        print(f"ID: {exchange_data_response.get('id')}")
        print(f"Points: {exchange_data_response.get('points')}")
        print(f"Code: {exchange_data_response.get('exchange_code')}")
        return True
    else:
        print(f"❌ Erreur lors de la création de la demande d'échange")
        return False

if __name__ == "__main__":
    test_exchange_creation()
