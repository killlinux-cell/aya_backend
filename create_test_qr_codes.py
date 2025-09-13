#!/usr/bin/env python3
"""
Script pour créer des QR codes de test pour l'application Aya
Usage: python manage.py shell
Puis copier-coller le contenu de ce script
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from qr_codes.models import QRCode, UserQRCode
import random
import string

def create_test_qr_codes():
    """Créer des QR codes de test avec différents types de récompenses"""
    
    # Types de récompenses
    prize_types = [
        {'points': 10, 'description': 'Petit gain - 10 points'},
        {'points': 25, 'description': 'Gain moyen - 25 points'},
        {'points': 50, 'description': 'Bon gain - 50 points'},
        {'points': 100, 'description': 'Excellent gain - 100 points'},
        {'points': 0, 'description': 'Ticket fidélité', 'is_loyalty': True},
    ]
    
    # Créer 20 QR codes de test
    for i in range(20):
        # Générer un code unique
        code = f"TEST_{i+1:03d}_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
        
        # Choisir un type de prix aléatoire
        prize = random.choice(prize_types)
        
        # Créer le QR code
        qr_code = QRCode.objects.create(
            code=code,
            points=prize['points'],
            description=prize['description'],
            is_active=True
        )
        
        print(f"✅ QR Code créé: {code} - {prize['description']}")
    
    print(f"\n🎯 {20} QR codes de test créés avec succès !")
    print("\n📱 Pour tester dans l'app Flutter:")
    print("1. Ouvrez l'app sur votre téléphone")
    print("2. Allez dans 'Scanner'")
    print("3. Scannez un des codes créés")
    print("4. Vérifiez que le popup de récompense s'affiche")

def create_specific_test_codes():
    """Créer des QR codes spécifiques pour des tests précis"""
    
    test_codes = [
        {'code': 'TEST_WIN_001', 'points': 50, 'description': 'Test gain 50 points', 'prize_type': 'points'},
        {'code': 'TEST_WIN_002', 'points': 100, 'description': 'Test gain 100 points', 'prize_type': 'points'},
        {'code': 'TEST_LOYALTY_001', 'points': 0, 'description': 'Test ticket fidélité', 'prize_type': 'loyalty_ticket'},
        {'code': 'TEST_LOYALTY_002', 'points': 0, 'description': 'Test ticket fidélité 2', 'prize_type': 'loyalty_ticket'},
        {'code': 'TEST_ALREADY_USED', 'points': 25, 'description': 'Test code déjà utilisé', 'prize_type': 'points'},
        {'code': 'TEST_INVALID', 'points': 10, 'description': 'Test code invalide', 'prize_type': 'points'},
    ]
    
    for test_code in test_codes:
        qr_code = QRCode.objects.create(
            code=test_code['code'],
            points=test_code['points'],
            description=test_code['description'],
            prize_type=test_code['prize_type'],
            is_active=True
        )
        
        # Marquer le code "TEST_ALREADY_USED" comme déjà utilisé
        if test_code['code'] == 'TEST_ALREADY_USED':
            # Créer un utilisateur de test s'il n'existe pas
            test_user, created = User.objects.get_or_create(
                email='test@example.com',
                defaults={
                    'first_name': 'Test',
                    'last_name': 'User',
                    'username': 'test_user'
                }
            )
            
            # Créer une entrée UserQRCode pour marquer comme utilisé
            from qr_codes.models import UserQRCode
            UserQRCode.objects.create(
                user=test_user,
                qr_code=qr_code,
                points_earned=qr_code.points
            )
        
        # Marquer le code "TEST_INVALID" comme inactif
        if test_code['code'] == 'TEST_INVALID':
            qr_code.is_active = False
            qr_code.save()
        
        print(f"✅ QR Code de test créé: {test_code['code']} - {test_code['description']}")

if __name__ == "__main__":
    print("🚀 Création des QR codes de test...")
    create_test_qr_codes()
    create_specific_test_codes()
    
    print("\n📋 Codes de test créés:")
    print("TEST_WIN_001 - 50 points")
    print("TEST_WIN_002 - 100 points") 
    print("TEST_LOYALTY_001 - Ticket fidélité")
    print("TEST_ALREADY_USED - Code déjà utilisé (pour tester l'erreur)")
    print("TEST_INVALID - Code invalide (pour tester l'erreur)")
    print("\n🎯 Vous pouvez maintenant tester ces codes dans l'app Flutter !")
