#!/usr/bin/env python3
"""
Script de test pour la restauration des points lors de l'expiration des tokens
"""

import os
import sys
import django
from datetime import timedelta

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from django.utils import timezone
from qr_codes.models import ExchangeToken
from authentication.models import User
from qr_codes.tasks import cleanup_expired_tokens

def test_token_restoration():
    """Teste la restauration des points lors de l'expiration des tokens"""
    
    print("🧪 Test de restauration des points pour tokens expirés")
    print("=" * 60)
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'full_name': 'Test User',
            'available_points': 1000,
            'exchanged_points': 0
        }
    )
    
    if created:
        print(f"✅ Utilisateur de test créé: {user.email}")
    else:
        print(f"✅ Utilisateur de test existant: {user.email}")
    
    print(f"   Points disponibles: {user.available_points}")
    
    # Créer un token expiré
    expired_time = timezone.now() - timedelta(minutes=5)  # Expiré il y a 5 minutes
    token = ExchangeToken.objects.create(
        user=user,
        points=100,
        token='TEST123456789',
        expires_at=expired_time,
        is_used=False
    )
    
    print(f"✅ Token expiré créé: {token.token}")
    print(f"   Points du token: {token.points}")
    print(f"   Expire à: {token.expires_at}")
    print(f"   Est expiré: {token.is_expired}")
    
    # Vérifier les points avant nettoyage
    user.refresh_from_db()
    points_before = user.available_points
    print(f"   Points avant nettoyage: {points_before}")
    
    # Nettoyer les tokens expirés
    print("\n🧹 Nettoyage des tokens expirés...")
    cleanup_expired_tokens()
    
    # Vérifier les points après nettoyage
    user.refresh_from_db()
    points_after = user.available_points
    print(f"   Points après nettoyage: {points_after}")
    
    # Vérifier que les points ont été restaurés
    if points_after == points_before + token.points:
        print("✅ Points restaurés avec succès!")
    else:
        print(f"❌ Erreur: Points attendus {points_before + token.points}, obtenus {points_after}")
    
    # Vérifier que le token a été supprimé
    try:
        ExchangeToken.objects.get(token=token.token)
        print("❌ Token non supprimé!")
    except ExchangeToken.DoesNotExist:
        print("✅ Token supprimé correctement!")
    
    # Nettoyer
    user.delete()
    print("\n🧹 Nettoyage terminé")
    
    print("\n" + "=" * 60)
    print("✅ Test terminé")

if __name__ == "__main__":
    test_token_restoration()
