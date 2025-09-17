#!/usr/bin/env python
"""
Script pour créer un grand prix de test
"""
import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from authentication.models import User
from authentication.models_grand_prix import GrandPrix, GrandPrixPrize

def create_grand_prix():
    """Créer un grand prix de test"""
    try:
        # Vérifier s'il existe déjà un grand prix actif
        now = timezone.now()
        existing_grand_prix = GrandPrix.objects.filter(
            start_date__lte=now,
            end_date__gte=now,
            status='active'
        ).first()
        
        if existing_grand_prix:
            print(f"ℹ️ Grand prix actif existe déjà : {existing_grand_prix.name}")
            return existing_grand_prix
        
        # Créer le grand prix
        start_date = now
        end_date = now + timedelta(days=30)  # 30 jours
        draw_date = end_date + timedelta(days=1)  # Tirage le lendemain
        
        grand_prix = GrandPrix.objects.create(
            name="Grand Prix AYA+ Janvier 2025",
            description="Participez au grand concours mensuel AYA+ et tentez de gagner des récompenses exceptionnelles !",
            participation_cost=100,  # 100 points pour participer
            start_date=start_date,
            end_date=end_date,
            draw_date=draw_date,
            status='active',
            created_by=User.objects.filter(is_superuser=True).first()
        )
        
        print(f"✅ Grand prix créé : {grand_prix.name}")
        
        # Créer les récompenses
        prizes_data = [
            {
                'position': 1,
                'name': 'iPhone 15 Pro',
                'description': 'Le dernier iPhone avec toutes les fonctionnalités premium',
                'value': 1200.00
            },
            {
                'position': 2,
                'name': 'AirPods Pro',
                'description': 'Écouteurs sans fil avec réduction de bruit active',
                'value': 280.00
            },
            {
                'position': 3,
                'name': 'Carte cadeau 100€',
                'description': 'Carte cadeau valable chez tous nos partenaires',
                'value': 100.00
            },
            {
                'position': 4,
                'name': 'Pack AYA+ Premium',
                'description': '500 points bonus + avantages VIP étendus',
                'value': 50.00
            },
            {
                'position': 5,
                'name': 'Réduction 20%',
                'description': 'Réduction de 20% sur tous vos échanges pendant 1 mois',
                'value': 25.00
            }
        ]
        
        for prize_data in prizes_data:
            prize = GrandPrixPrize.objects.create(
                grand_prix=grand_prix,
                **prize_data
            )
            print(f"✅ Récompense créée : {prize.get_position_display()} - {prize.name}")
        
        print(f"\n🎉 Grand prix '{grand_prix.name}' créé avec succès !")
        print(f"📅 Période : {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}")
        print(f"🎲 Tirage au sort : {draw_date.strftime('%d/%m/%Y à %H:%M')}")
        print(f"💰 Coût de participation : {grand_prix.participation_cost} points")
        print(f"🏆 Nombre de récompenses : {len(prizes_data)}")
        
        return grand_prix
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du grand prix : {e}")
        return None

def show_grand_prix_stats():
    """Afficher les statistiques du grand prix"""
    try:
        now = timezone.now()
        grand_prix = GrandPrix.objects.filter(
            start_date__lte=now,
            end_date__gte=now,
            status='active'
        ).first()
        
        if not grand_prix:
            print("❌ Aucun grand prix actif trouvé")
            return
        
        participants = grand_prix.participations.all()
        winners = participants.filter(is_winner=True)
        
        print(f"\n📊 Statistiques du Grand Prix : {grand_prix.name}")
        print("=" * 50)
        print(f"👥 Nombre de participants : {participants.count()}")
        print(f"🏆 Nombre de gagnants : {winners.count()}")
        print(f"💰 Points collectés : {sum(p.points_spent for p in participants)}")
        print(f"📅 Jours restants : {(grand_prix.end_date - now).days} jours")
        
        if participants.exists():
            print(f"\n👥 Participants récents :")
            for participation in participants.order_by('-participated_at')[:5]:
                print(f"  • {participation.user.email} - {participation.participated_at.strftime('%d/%m/%Y %H:%M')}")
        
        if winners.exists():
            print(f"\n🏆 Gagnants :")
            for winner in winners:
                prize_info = f" ({winner.prize_won.name})" if winner.prize_won else ""
                print(f"  • {winner.user.email}{prize_info}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'affichage des statistiques : {e}")

def main():
    """Fonction principale"""
    print("🏆 Création du Grand Prix AYA+...")
    print("=" * 50)
    
    try:
        # Créer le grand prix
        grand_prix = create_grand_prix()
        
        if grand_prix:
            # Afficher les statistiques
            show_grand_prix_stats()
            
            print("\n" + "=" * 50)
            print("✅ Grand prix configuré avec succès !")
            print("\n🌐 Accédez à l'admin Django pour gérer le grand prix :")
            print("   http://localhost:8000/admin/authentication/grandprix/")
            print("\n📱 Les utilisateurs VIP peuvent maintenant participer via l'app mobile !")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
