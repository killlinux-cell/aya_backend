#!/usr/bin/env python
"""
Script pour ajouter des coordonnées GPS aux vendeurs existants
"""
import os
import sys
import django
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from authentication.models import Vendor
import random

def add_vendor_coordinates():
    """Ajouter des coordonnées GPS aux vendeurs existants"""
    try:
        print("🗺️ Ajout de coordonnées GPS aux vendeurs...")
        print("=" * 50)
        
        # Coordonnées de villes en Côte d'Ivoire
        city_coordinates = {
            'Abidjan': {'lat': 5.3600, 'lng': -4.0083},
            'Yamoussoukro': {'lat': 6.8276, 'lng': -5.2893},
            'Bouaké': {'lat': 7.6944, 'lng': -5.0303},
            'San-Pédro': {'lat': 4.7485, 'lng': -6.6363},
            'Korhogo': {'lat': 9.4580, 'lng': -5.6296},
            'Man': {'lat': 7.4125, 'lng': -7.5533},
            'Gagnoa': {'lat': 6.1289, 'lng': -5.9506},
            'Divo': {'lat': 5.8431, 'lng': -5.3572},
            'Anyama': {'lat': 5.4944, 'lng': -4.0517},
            'Abengourou': {'lat': 6.7297, 'lng': -3.4964},
        }
        
        vendors = Vendor.objects.all()
        updated_count = 0
        
        for vendor in vendors:
            # Si le vendeur a déjà des coordonnées, passer
            if vendor.latitude and vendor.longitude and vendor.latitude != 0 and vendor.longitude != 0:
                print(f"ℹ️ {vendor.business_name} a déjà des coordonnées")
                continue
            
            # Déterminer la ville basée sur le nom ou la région
            city = None
            for city_name in city_coordinates.keys():
                if (city_name.lower() in vendor.city.lower() or 
                    city_name.lower() in vendor.region.lower() or
                    city_name.lower() in vendor.business_address.lower()):
                    city = city_name
                    break
            
            # Si aucune ville trouvée, utiliser Abidjan par défaut
            if not city:
                city = 'Abidjan'
            
            # Obtenir les coordonnées de base
            base_lat = city_coordinates[city]['lat']
            base_lng = city_coordinates[city]['lng']
            
            # Ajouter une variation aléatoire pour simuler des positions différentes
            lat_variation = random.uniform(-0.05, 0.05)  # ~5km de variation
            lng_variation = random.uniform(-0.05, 0.05)
            
            vendor.latitude = base_lat + lat_variation
            vendor.longitude = base_lng + lng_variation
            
            # Mettre à jour la ville si elle était vide
            if not vendor.city:
                vendor.city = city
            
            vendor.save()
            updated_count += 1
            
            print(f"✅ {vendor.business_name} - {city} ({vendor.latitude:.4f}, {vendor.longitude:.4f})")
        
        print("=" * 50)
        print(f"🎉 {updated_count} vendeurs mis à jour avec des coordonnées GPS")
        
        # Afficher un résumé par ville
        print("\n📊 Résumé par ville:")
        for city, coords in city_coordinates.items():
            count = Vendor.objects.filter(
                city__icontains=city,
                latitude__isnull=False,
                longitude__isnull=False
            ).exclude(latitude=0, longitude=0).count()
            if count > 0:
                print(f"  • {city}: {count} vendeur(s)")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout des coordonnées: {e}")
        sys.exit(1)

def show_vendor_locations():
    """Afficher les positions des vendeurs"""
    try:
        print("\n🗺️ Positions des vendeurs:")
        print("=" * 50)
        
        vendors = Vendor.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).exclude(latitude=0, longitude=0)
        
        for vendor in vendors:
            print(f"🏪 {vendor.business_name}")
            print(f"   📍 {vendor.city}, {vendor.region}")
            print(f"   🗺️ {vendor.latitude:.4f}, {vendor.longitude:.4f}")
            print(f"   📞 {vendor.phone_number}")
            print(f"   🏠 {vendor.business_address}")
            print()
        
        print(f"Total: {vendors.count()} vendeurs avec coordonnées GPS")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'affichage des positions: {e}")

def main():
    """Fonction principale"""
    print("🗺️ Gestion des coordonnées GPS des vendeurs")
    print("=" * 50)
    
    try:
        # Ajouter des coordonnées
        add_vendor_coordinates()
        
        # Afficher les positions
        show_vendor_locations()
        
        print("\n✅ Script terminé avec succès !")
        print("\n🌐 Les vendeurs sont maintenant visibles sur la carte dans l'app mobile !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
