#!/usr/bin/env python3
"""
Script de test pour l'API du jeu scratch&win
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000/api"
GAME_ENDPOINT = f"{BASE_URL}/games/play/"

def test_scratch_game():
    """Teste l'endpoint du jeu scratch&win"""
    
    print("🧪 Test de l'API Scratch & Win")
    print("=" * 50)
    
    # Test 1: Vérifier que l'endpoint existe
    print("1. Test de l'endpoint...")
    try:
        response = requests.get(GAME_ENDPOINT, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 405:  # Method Not Allowed est normal pour GET
            print("   ✅ Endpoint accessible (GET non autorisé, c'est normal)")
        else:
            print(f"   ⚠️  Réponse inattendue: {response.text}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter au serveur")
        print("   💡 Assurez-vous que le serveur Django est démarré")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 2: Test avec des données de jeu (sans authentification)
    print("\n2. Test avec des données de jeu (sans auth)...")
    game_data = {
        "game_type": "scratch_and_win",
        "points_cost": 10
    }
    
    try:
        response = requests.post(
            GAME_ENDPOINT,
            json=game_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Réponse: {response.text}")
        
        if response.status_code == 401:
            print("   ✅ Authentification requise (comportement attendu)")
        else:
            print(f"   ⚠️  Réponse inattendue")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 3: Vérifier la structure de l'API
    print("\n3. Test de la structure de l'API...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ API accessible")
            print(f"   Endpoints disponibles: {list(data.get('endpoints', {}).keys())}")
        else:
            print(f"   ⚠️  API non accessible: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur API: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Tests terminés")
    return True

if __name__ == "__main__":
    test_scratch_game()
