from django.urls import path
from . import views

urlpatterns = [
    # Authentification vendeurs
    path('login/', views.VendorLoginView.as_view(), name='vendor_login'),
    path('profile/', views.VendorProfileView.as_view(), name='vendor_profile'),
    
    # Informations client (pour vendeurs)
    path('client/<int:user_id>/', views.ClientInfoView.as_view(), name='client_info'),
]
