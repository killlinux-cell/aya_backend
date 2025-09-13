#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aya_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Créer un superutilisateur
if not User.objects.filter(email='admin@aya.com').exists():
    User.objects.create_superuser(
        email='admin@aya.com',
        password='admin123',
        first_name='Admin',
        last_name='Aya'
    )
    print("✅ Superutilisateur créé avec succès !")
    print("📧 Email: admin@aya.com")
    print("🔑 Mot de passe: admin123")
else:
    print("ℹ️  Le superutilisateur existe déjà.")
