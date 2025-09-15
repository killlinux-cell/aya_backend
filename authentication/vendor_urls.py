from django.urls import path
from . import views

urlpatterns = [
    # Authentification vendeurs
    path('login/', views.VendorLoginView.as_view(), name='vendor_login'),
    path('profile/', views.VendorProfileView.as_view(), name='vendor_profile'),
    
    # Informations client (pour vendeurs)
    path('client/<int:user_id>/', views.ClientInfoView.as_view(), name='client_info'),
    
    # Vendeurs disponibles (pour les utilisateurs)
    path('available/', views.available_vendors, name='available_vendors'),
    path('search/', views.search_vendors, name='search_vendors'),
    
    # Historique des échanges pour les vendeurs
    path('exchange-history/', views.vendor_exchange_history, name='vendor_exchange_history'),
]
