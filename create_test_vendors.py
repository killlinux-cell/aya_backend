#!/usr/bin/env python
"""
Script pour créer des vendeurs de test
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from authentication.models import User, Vendor
from django.contrib.auth.hashers import make_password

def create_test_vendors():
    """Créer des vendeurs de test"""
    
    # Vendeur 1: Supermarché
    user1, created1 = User.objects.get_or_create(
        email='vendeur1@aya.com',
        defaults={
            'first_name': 'Marie',
            'last_name': 'Dubois',
            'username': 'vendeur1@aya.com',
            'password': make_password('vendeur123'),
            'is_active': True,
        }
    )
    
    if created1:
        vendor1, _ = Vendor.objects.get_or_create(
            user=user1,
            defaults={
                'vendor_code': 'VEN001',
                'business_name': 'Supermarché Aya Plus',
                'business_address': '123 Avenue des Champs, Paris 75001',
                'phone_number': '+33 1 23 45 67 89',
                'status': 'active',
            }
        )
        print(f'✅ Vendeur créé: {vendor1.business_name} ({vendor1.vendor_code})')
    else:
        print(f'⚠️  Utilisateur vendeur1@aya.com existe déjà')
    
    # Vendeur 2: Pharmacie
    user2, created2 = User.objects.get_or_create(
        email='vendeur2@aya.com',
        defaults={
            'first_name': 'Pierre',
            'last_name': 'Martin',
            'username': 'vendeur2@aya.com',
            'password': make_password('vendeur123'),
            'is_active': True,
        }
    )
    
    if created2:
        vendor2, _ = Vendor.objects.get_or_create(
            user=user2,
            defaults={
                'vendor_code': 'VEN002',
                'business_name': 'Pharmacie Centrale',
                'business_address': '456 Rue de la Paix, Lyon 69001',
                'phone_number': '+33 4 56 78 90 12',
                'status': 'active',
            }
        )
        print(f'✅ Vendeur créé: {vendor2.business_name} ({vendor2.vendor_code})')
    else:
        print(f'⚠️  Utilisateur vendeur2@aya.com existe déjà')
    
    # Vendeur 3: Boulangerie
    user3, created3 = User.objects.get_or_create(
        email='vendeur3@aya.com',
        defaults={
            'first_name': 'Sophie',
            'last_name': 'Leroy',
            'username': 'vendeur3@aya.com',
            'password': make_password('vendeur123'),
            'is_active': True,
        }
    )
    
    if created3:
        vendor3, _ = Vendor.objects.get_or_create(
            user=user3,
            defaults={
                'vendor_code': 'VEN003',
                'business_name': 'Boulangerie du Coin',
                'business_address': '789 Place du Marché, Marseille 13001',
                'phone_number': '+33 4 91 23 45 67',
                'status': 'active',
            }
        )
        print(f'✅ Vendeur créé: {vendor3.business_name} ({vendor3.vendor_code})')
    else:
        print(f'⚠️  Utilisateur vendeur3@aya.com existe déjà')
    
    print('\n📋 Informations de connexion des vendeurs:')
    print('=' * 50)
    print('Vendeur 1:')
    print('  Email: vendeur1@aya.com')
    print('  Mot de passe: vendeur123')
    print('  Code: VEN001')
    print()
    print('Vendeur 2:')
    print('  Email: vendeur2@aya.com')
    print('  Mot de passe: vendeur123')
    print('  Code: VEN002')
    print()
    print('Vendeur 3:')
    print('  Email: vendeur3@aya.com')
    print('  Mot de passe: vendeur123')
    print('  Code: VEN003')
    print('=' * 50)

if __name__ == '__main__':
    create_test_vendors()
