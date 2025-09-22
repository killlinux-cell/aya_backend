#!/usr/bin/env python3
"""
Script de nettoyage manuel des tokens d'échange expirés
Usage: python cleanup_tokens.py [--dry-run]
"""

import os
import sys
import django
import argparse

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from qr_codes.tasks import cleanup_expired_tokens

def main():
    parser = argparse.ArgumentParser(description='Nettoie les tokens d\'échange expirés')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Simule le nettoyage sans effectuer les modifications')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🧪 Mode simulation - aucune modification ne sera effectuée")
        # TODO: Implémenter le mode dry-run dans cleanup_expired_tokens
        return
    
    print("🧹 Nettoyage des tokens d'échange expirés...")
    cleanup_expired_tokens()
    print("✅ Nettoyage terminé!")

if __name__ == "__main__":
    main()
