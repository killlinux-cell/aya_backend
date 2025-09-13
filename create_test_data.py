#!/usr/bin/env python
"""
Script pour créer des données de test pour l'application Aya
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from authentication.models import User
from qr_codes.models import QRCode, UserQRCode, GameHistory, ExchangeRequest
from django.utils import timezone
import uuid


def create_test_users():
    """Créer des utilisateurs de test"""
    print("Création des utilisateurs de test...")
    
    # Utilisateur de démonstration
    demo_user, created = User.objects.get_or_create(
        email='demo@example.com',
        defaults={
            'username': 'demo_user',
            'first_name': 'Demo',
            'last_name': 'User',
            'available_points': 100,
            'exchanged_points': 50,
            'collected_qr_codes': 5,
            'personal_qr_code': 'DEMO_QR_12345',
        }
    )
    
    if created:
        demo_user.set_password('password')
        demo_user.save()
        print(f"✅ Utilisateur de démo créé: {demo_user.email}")
    else:
        print(f"ℹ️  Utilisateur de démo existe déjà: {demo_user.email}")
    
    # Utilisateur test
    test_user, created = User.objects.get_or_create(
        email='test@aya.com',
        defaults={
            'username': 'test_user',
            'first_name': 'Test',
            'last_name': 'User',
            'available_points': 200,
            'exchanged_points': 30,
            'collected_qr_codes': 8,
            'personal_qr_code': 'TEST_QR_67890',
        }
    )
    
    if created:
        test_user.set_password('test123')
        test_user.save()
        print(f"✅ Utilisateur test créé: {test_user.email}")
    else:
        print(f"ℹ️  Utilisateur test existe déjà: {test_user.email}")
    
    return demo_user, test_user


def create_test_qr_codes():
    """Créer des QR codes de test"""
    print("Création des QR codes de test...")
    
    qr_codes_data = [
        {
            'code': 'VALID_QR_CODE',
            'points': 50,
            'description': 'QR Code de démonstration valide',
            'is_active': True,
        },
        {
            'code': 'BONUS_QR_100',
            'points': 100,
            'description': 'QR Code bonus - 100 points',
            'is_active': True,
        },
        {
            'code': 'SMALL_QR_10',
            'points': 10,
            'description': 'QR Code petit - 10 points',
            'is_active': True,
        },
        {
            'code': 'EXPIRED_QR',
            'points': 25,
            'description': 'QR Code expiré',
            'is_active': False,
        },
        {
            'code': 'ALREADY_USED',
            'points': 30,
            'description': 'QR Code déjà utilisé',
            'is_active': True,
        },
    ]
    
    created_count = 0
    for qr_data in qr_codes_data:
        qr_code, created = QRCode.objects.get_or_create(
            code=qr_data['code'],
            defaults=qr_data
        )
        if created:
            created_count += 1
            print(f"✅ QR Code créé: {qr_code.code} ({qr_code.points} points)")
        else:
            print(f"ℹ️  QR Code existe déjà: {qr_code.code}")
    
    print(f"📊 Total QR codes créés: {created_count}")
    return QRCode.objects.all()


def create_test_user_qr_codes(demo_user, qr_codes):
    """Créer des associations utilisateur-QR code"""
    print("Création des associations utilisateur-QR code...")
    
    # Associer quelques QR codes à l'utilisateur de démo
    demo_qr_codes = qr_codes.filter(code__in=['VALID_QR_CODE', 'BONUS_QR_100'])
    
    created_count = 0
    for qr_code in demo_qr_codes:
        user_qr_code, created = UserQRCode.objects.get_or_create(
            user=demo_user,
            qr_code=qr_code,
            defaults={
                'points_earned': qr_code.points,
                'scanned_at': timezone.now(),
            }
        )
        if created:
            created_count += 1
            print(f"✅ Association créée: {demo_user.email} -> {qr_code.code}")
        else:
            print(f"ℹ️  Association existe déjà: {demo_user.email} -> {qr_code.code}")
    
    print(f"📊 Total associations créées: {created_count}")


def create_test_game_history(demo_user):
    """Créer un historique de jeux de test"""
    print("Création de l'historique de jeux...")
    
    game_history_data = [
        {
            'game_type': 'scratch_win',
            'points_spent': 10,
            'points_won': 20,
            'is_winning': True,
            'played_at': timezone.now().replace(hour=10, minute=30),
        },
        {
            'game_type': 'spin_wheel',
            'points_spent': 10,
            'points_won': 0,
            'is_winning': False,
            'played_at': timezone.now().replace(hour=14, minute=15),
        },
        {
            'game_type': 'scratch_win',
            'points_spent': 10,
            'points_won': 15,
            'is_winning': True,
            'played_at': timezone.now().replace(hour=16, minute=45),
        },
    ]
    
    created_count = 0
    for game_data in game_history_data:
        game_history, created = GameHistory.objects.get_or_create(
            user=demo_user,
            game_type=game_data['game_type'],
            points_spent=game_data['points_spent'],
            points_won=game_data['points_won'],
            played_at=game_data['played_at'],
            defaults=game_data
        )
        if created:
            created_count += 1
            print(f"✅ Historique de jeu créé: {game_data['game_type']} - {game_data['points_won']} points")
        else:
            print(f"ℹ️  Historique de jeu existe déjà: {game_data['game_type']}")
    
    print(f"📊 Total historiques de jeux créés: {created_count}")


def create_test_exchange_requests(demo_user):
    """Créer des demandes d'échange de test"""
    print("Création des demandes d'échange...")
    
    exchange_data = [
        {
            'points': 30,
            'exchange_code': 'EXCH_DEMO_001',
            'status': 'completed',
            'created_at': timezone.now().replace(hour=9, minute=0),
            'completed_at': timezone.now().replace(hour=9, minute=30),
        },
        {
            'points': 20,
            'exchange_code': 'EXCH_DEMO_002',
            'status': 'pending',
            'created_at': timezone.now().replace(hour=15, minute=0),
        },
    ]
    
    created_count = 0
    for exchange_info in exchange_data:
        exchange_request, created = ExchangeRequest.objects.get_or_create(
            user=demo_user,
            exchange_code=exchange_info['exchange_code'],
            defaults=exchange_info
        )
        if created:
            created_count += 1
            print(f"✅ Demande d'échange créée: {exchange_info['exchange_code']} - {exchange_info['points']} points")
        else:
            print(f"ℹ️  Demande d'échange existe déjà: {exchange_info['exchange_code']}")
    
    print(f"📊 Total demandes d'échange créées: {created_count}")


def main():
    """Fonction principale"""
    print("🚀 Création des données de test pour l'application Aya")
    print("=" * 60)
    
    try:
        # Créer les utilisateurs
        demo_user, test_user = create_test_users()
        print()
        
        # Créer les QR codes
        qr_codes = create_test_qr_codes()
        print()
        
        # Créer les associations utilisateur-QR code
        create_test_user_qr_codes(demo_user, qr_codes)
        print()
        
        # Créer l'historique de jeux
        create_test_game_history(demo_user)
        print()
        
        # Créer les demandes d'échange
        create_test_exchange_requests(demo_user)
        print()
        
        print("=" * 60)
        print("✅ Toutes les données de test ont été créées avec succès !")
        print()
        print("📋 Résumé des comptes de test :")
        print(f"   • Email: demo@example.com | Mot de passe: password")
        print(f"   • Email: test@aya.com | Mot de passe: test123")
        print()
        print("🔑 QR Codes de test :")
        print(f"   • VALID_QR_CODE (50 points)")
        print(f"   • BONUS_QR_100 (100 points)")
        print(f"   • SMALL_QR_10 (10 points)")
        print(f"   • ALREADY_USED (30 points - déjà utilisé)")
        print()
        print("🎮 Codes d'échange de test :")
        print(f"   • EXCH_DEMO_001 (30 points - complété)")
        print(f"   • EXCH_DEMO_002 (20 points - en attente)")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données de test: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
