import os
import django
from datetime import timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from django.utils import timezone
from authentication.models_grand_prix import GrandPrix, GrandPrixPrize

def create_grand_prix():
    """Créer un Grand Prix test"""
    
    # Vérifier si un Grand Prix actif existe déjà
    existing = GrandPrix.objects.filter(status='active').first()
    if existing:
        print(f"[!] Un Grand Prix actif existe deja: {existing.name}")
        print(f"[+] Actif du {existing.start_date.strftime('%d/%m/%Y')} au {existing.end_date.strftime('%d/%m/%Y')}")
        return
    
    # Créer le Grand Prix
    grand_prix = GrandPrix.objects.create(
        name="Trésor de Mon Pays",
        description="Collectez 100 points et tentez de remporter le trésor !",
        participation_cost=100,
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=30),
        draw_date=timezone.now() + timedelta(days=30),
        status='active'
    )
    
    print(f"[OK] Grand Prix cree: {grand_prix.name}")
    
    # Créer les récompenses
    prizes = [
        {'position': 1, 'name': 'Trésor d\'Or', 'description': 'Premier prix', 'value': 1000},
        {'position': 2, 'name': 'Trésor d\'Argent', 'description': 'Deuxième prix', 'value': 500},
        {'position': 3, 'name': 'Trésor de Bronze', 'description': 'Troisième prix', 'value': 250},
    ]
    
    for prize_data in prizes:
        GrandPrixPrize.objects.create(
            grand_prix=grand_prix,
            **prize_data
        )
        print(f"[OK] Recompense creee: {prize_data['name']}")
    
    print(f"\n[SUCCESS] Grand Prix '{grand_prix.name}' cree avec succes!")
    print(f"[DATE] Actif du {grand_prix.start_date.strftime('%d/%m/%Y')} au {grand_prix.end_date.strftime('%d/%m/%Y')}")
    print(f"[COST] Cout de participation: {grand_prix.participation_cost} points")

if __name__ == '__main__':
    create_grand_prix()

