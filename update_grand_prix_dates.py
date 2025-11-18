import os
import django
from datetime import timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from django.utils import timezone
from authentication.models_grand_prix import GrandPrix

def update_grand_prix_dates():
    """Mettre à jour les dates du Grand Prix pour le rendre actif"""
    
    # Récupérer tous les Grand Prix
    all_gp = GrandPrix.objects.all()
    print(f"[INFO] {all_gp.count()} Grand Prix trouves dans la base de donnees\n")
    
    if all_gp.count() == 0:
        print("[ERROR] Aucun Grand Prix trouve ! Executez create_grand_prix_quick.py d'abord.")
        return
    
    for gp in all_gp:
        print(f"[GP] {gp.name}")
        print(f"     Dates actuelles : {gp.start_date.strftime('%d/%m/%Y')} - {gp.end_date.strftime('%d/%m/%Y')}")
        print(f"     Status : {gp.status}")
        
        # Vérifier si expiré
        now = timezone.now()
        if gp.end_date < now:
            print(f"     [!] Grand Prix EXPIRE (fin : {gp.end_date.strftime('%d/%m/%Y')})")
        
        # Mettre à jour les dates
        gp.start_date = timezone.now()
        gp.end_date = timezone.now() + timedelta(days=30)
        gp.draw_date = timezone.now() + timedelta(days=30)
        gp.status = 'active'
        gp.save()
        
        print(f"     [OK] Dates mises a jour : {gp.start_date.strftime('%d/%m/%Y')} - {gp.end_date.strftime('%d/%m/%Y')}")
        print(f"     [OK] Status : {gp.status}")
        print()
    
    print(f"[SUCCESS] {all_gp.count()} Grand Prix mis a jour et actifs !")
    print(f"[INFO] Ils sont maintenant actifs pour les 30 prochains jours.")

if __name__ == '__main__':
    update_grand_prix_dates()

