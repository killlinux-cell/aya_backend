from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_home, name='home'),
    
    # Gestion des QR codes
    path('qr-codes/', views.qr_codes_management, name='qr_codes'),
    path('qr-codes/create/', views.create_qr_code, name='create_qr_code'),
    path('qr-codes/<uuid:qr_code_id>/edit/', views.edit_qr_code, name='edit_qr_code'),
    path('qr-codes/<uuid:qr_code_id>/delete/', views.delete_qr_code, name='delete_qr_code'),
    path('qr-codes/<uuid:qr_code_id>/generate/', views.generate_qr_code_image, name='generate_qr_code'),
    path('qr-codes/<uuid:qr_code_id>/download/', views.download_qr_code, name='download_qr_code'),
    path('qr-codes/bulk-generate/', views.bulk_generate_qr_codes, name='bulk_generate_qr_codes'),
    
    # Gestion des utilisateurs
    path('users/', views.users_management, name='users'),
    
    # Analytics
    path('analytics/', views.analytics, name='analytics'),
    
    # Demandes d'échange
    path('exchanges/', views.exchange_requests, name='exchanges'),
    path('exchanges/<uuid:exchange_id>/update-status/', views.update_exchange_status, name='update_exchange_status'),
    
    # Gestion des vendeurs
    path('vendors/', views.vendors_management, name='vendors'),
    path('vendors/create/', views.create_vendor, name='create_vendor'),
    path('vendors/<uuid:vendor_id>/update-status/', views.update_vendor_status, name='update_vendor_status'),
    
    # Gestion des jeux
    path('games/', views.games_management, name='games'),
    
    # Gestion des tokens d'échange
    path('exchange-tokens/', views.exchange_tokens_management, name='exchange_tokens'),
    
    # Nouvelles fonctionnalités
    path('qr-codes-analytics/', views.qr_codes_analytics, name='qr_codes_analytics'),
    path('system-health/', views.system_health, name='system_health'),
    path('bulk-operations/', views.bulk_operations, name='bulk_operations'),
]
