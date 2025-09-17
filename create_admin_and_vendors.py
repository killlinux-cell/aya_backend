#!/usr/bin/env python
"""
Script pour créer un superutilisateur et des vendeurs de test
"""
import os
import sys
import django
from django.contrib.auth import get_user_model
from django.db import transaction

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from authentication.models import User, Vendor

def create_superuser():
    """Créer un superutilisateur admin"""
    User = get_user_model()
    
    if not User.objects.filter(email='admin@aya.com').exists():
        User.objects.create_superuser(
            email='admin@aya.com',
            password='admin123',
            first_name='Admin',
            last_name='AYA'
        )
        print("✅ Superutilisateur créé : admin@aya.com / admin123")
    else:
        print("ℹ️ Superutilisateur admin@aya.com existe déjà")

def create_test_vendors():
    """Créer des vendeurs de test"""
    vendors_data = [
        {
            'email': 'vendeur1@aya.com',
            'password': 'vendeur123',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'business_name': 'Restaurant Le Bon Goût',
            'business_address': '123 Avenue de la Paix, Abidjan',
            'phone_number': '+225 07 12 34 56 78',
            'city': 'Abidjan',
            'region': 'Lagunes',
            'country': 'Côte d\'Ivoire'
        },
        {
            'email': 'vendeur2@aya.com',
            'password': 'vendeur123',
            'first_name': 'Marie',
            'last_name': 'Kouassi',
            'business_name': 'Boutique Mode & Style',
            'business_address': '456 Rue du Commerce, Yamoussoukro',
            'phone_number': '+225 07 23 45 67 89',
            'city': 'Yamoussoukro',
            'region': 'Yamoussoukro',
            'country': 'Côte d\'Ivoire'
        },
        {
            'email': 'vendeur3@aya.com',
            'password': 'vendeur123',
            'first_name': 'Kouame',
            'last_name': 'Traore',
            'business_name': 'Super Marché Central',
            'business_address': '789 Boulevard de la République, Bouaké',
            'phone_number': '+225 07 34 56 78 90',
            'city': 'Bouaké',
            'region': 'Vallée du Bandama',
            'country': 'Côte d\'Ivoire'
        },
        {
            'email': 'vendeur4@aya.com',
            'password': 'vendeur123',
            'first_name': 'Fatou',
            'last_name': 'Diabate',
            'business_name': 'Pharmacie du Centre',
            'business_address': '321 Avenue Nangui Abrogoua, Abidjan',
            'phone_number': '+225 07 45 67 89 01',
            'city': 'Abidjan',
            'region': 'Lagunes',
            'country': 'Côte d\'Ivoire'
        },
        {
            'email': 'vendeur5@aya.com',
            'password': 'vendeur123',
            'first_name': 'Amadou',
            'last_name': 'Sangare',
            'business_name': 'Station Service Total',
            'business_address': '654 Route de Bassam, Abidjan',
            'phone_number': '+225 07 56 78 90 12',
            'city': 'Abidjan',
            'region': 'Lagunes',
            'country': 'Côte d\'Ivoire'
        }
    ]
    
    created_count = 0
    for vendor_data in vendors_data:
        email = vendor_data.pop('email')
        password = vendor_data.pop('password')
        
        # Créer l'utilisateur
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': vendor_data['first_name'],
                'last_name': vendor_data['last_name'],
                'is_active': True
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            print(f"✅ Utilisateur créé : {email}")
        else:
            print(f"ℹ️ Utilisateur {email} existe déjà")
        
        # Créer le profil vendeur
        vendor, vendor_created = Vendor.objects.get_or_create(
            user=user,
            defaults=vendor_data
        )
        
        if vendor_created:
            created_count += 1
            print(f"✅ Vendeur créé : {vendor.business_name} ({vendor.vendor_code})")
        else:
            print(f"ℹ️ Vendeur {vendor.business_name} existe déjà")
    
    print(f"\n🎉 {created_count} nouveau(x) vendeur(s) créé(s)")

def create_test_users():
    """Créer des utilisateurs de test"""
    users_data = [
        {
            'email': 'client1@aya.com',
            'password': 'client123',
            'first_name': 'Alice',
            'last_name': 'Martin',
            'available_points': 150
        },
        {
            'email': 'client2@aya.com',
            'password': 'client123',
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'available_points': 75
        },
        {
            'email': 'client3@aya.com',
            'password': 'client123',
            'first_name': 'Charlie',
            'last_name': 'Brown',
            'available_points': 200
        }
    ]
    
    created_count = 0
    for user_data in users_data:
        email = user_data.pop('email')
        password = user_data.pop('password')
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults=user_data
        )
        
        if created:
            user.set_password(password)
            user.save()
            created_count += 1
            print(f"✅ Client créé : {email} ({user.available_points} points)")
        else:
            print(f"ℹ️ Client {email} existe déjà")
    
    print(f"\n🎉 {created_count} nouveau(x) client(s) créé(s)")

def main():
    """Fonction principale"""
    print("🚀 Création des utilisateurs et vendeurs de test...")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            # Créer le superutilisateur
            create_superuser()
            print()
            
            # Créer les vendeurs de test
            create_test_vendors()
            print()
            
            # Créer les clients de test
            create_test_users()
            print()
            
        print("=" * 50)
        print("✅ Tous les utilisateurs ont été créés avec succès !")
        print("\n📋 Informations de connexion :")
        print("Admin : admin@aya.com / admin123")
        print("Vendeurs : vendeur1@aya.com à vendeur5@aya.com / vendeur123")
        print("Clients : client1@aya.com à client3@aya.com / client123")
        print("\n🌐 Accédez à l'admin Django : http://localhost:8000/admin/")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
