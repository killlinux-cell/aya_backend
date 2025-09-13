from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import User
from qr_codes.models import QRCode, UserQRCode
import random
import string

class Command(BaseCommand):
    help = 'Créer des QR codes de test pour l\'application Aya'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Création des QR codes de test...'))
        
        # Créer des QR codes de test
        self.create_test_qr_codes()
        self.create_specific_test_codes()
        
        self.stdout.write(self.style.SUCCESS('\n📋 Codes de test créés:'))
        self.stdout.write('TEST_WIN_001 - 50 points')
        self.stdout.write('TEST_WIN_002 - 100 points') 
        self.stdout.write('TEST_LOYALTY_001 - Ticket fidélité')
        self.stdout.write('TEST_ALREADY_USED - Code déjà utilisé (pour tester l\'erreur)')
        self.stdout.write('TEST_INVALID - Code invalide (pour tester l\'erreur)')
        self.stdout.write(self.style.SUCCESS('\n🎯 Vous pouvez maintenant tester ces codes dans l\'app Flutter !'))

    def create_test_qr_codes(self):
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
            
            self.stdout.write(f'✅ QR Code créé: {code} - {prize["description"]}')
        
        self.stdout.write(self.style.SUCCESS(f'\n🎯 {20} QR codes de test créés avec succès !'))

    def create_specific_test_codes(self):
        """Créer des QR codes spécifiques pour des tests précis"""
        
        test_codes = [
            {'code': 'TEST_WIN_001', 'points': 50, 'description': 'Test gain 50 points'},
            {'code': 'TEST_WIN_002', 'points': 100, 'description': 'Test gain 100 points'},
            {'code': 'TEST_LOYALTY_001', 'points': 0, 'description': 'Test ticket fidélité'},
            {'code': 'TEST_ALREADY_USED', 'points': 25, 'description': 'Test code déjà utilisé'},
            {'code': 'TEST_INVALID', 'points': 10, 'description': 'Test code invalide'},
        ]
        
        for test_code in test_codes:
            qr_code, created = QRCode.objects.get_or_create(
                code=test_code['code'],
                defaults={
                    'points': test_code['points'],
                    'description': test_code['description'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'✅ QR Code de test créé: {test_code["code"]} - {test_code["description"]}')
            else:
                self.stdout.write(f'⚠️ QR Code de test existe déjà: {test_code["code"]}')
            
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
                
                # Créer l'entrée UserQRCode pour marquer comme déjà utilisé
                UserQRCode.objects.get_or_create(
                    user=test_user,
                    qr_code=qr_code,
                    defaults={
                        'points_earned': 25
                    }
                )
                
                self.stdout.write(f'✅ Code {test_code["code"]} marqué comme déjà utilisé')
            
            # Marquer le code "TEST_INVALID" comme inactif
            if test_code['code'] == 'TEST_INVALID':
                qr_code.is_active = False
                qr_code.save()
                self.stdout.write(f'✅ Code {test_code["code"]} marqué comme invalide')
