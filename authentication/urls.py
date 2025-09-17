from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import grand_prix_views
from . import vendor_map_views

urlpatterns = [
    # Authentification
    path('register/', views.UserRegistrationView.as_view(), name='user_register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profil utilisateur
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('stats/', views.user_stats, name='user_stats'),
    
    # Gestion des mots de passe
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/request/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Grand Prix
    path('grand-prix/current/', grand_prix_views.get_current_grand_prix, name='get_current_grand_prix'),
    path('grand-prix/participate/', grand_prix_views.participate_in_grand_prix, name='participate_in_grand_prix'),
    path('grand-prix/my-participations/', grand_prix_views.get_user_participations, name='get_user_participations'),
    path('grand-prix/<uuid:grand_prix_id>/participants/', grand_prix_views.get_grand_prix_participants, name='get_grand_prix_participants'),
    path('grand-prix/<uuid:grand_prix_id>/draw/', grand_prix_views.conduct_grand_prix_draw, name='conduct_grand_prix_draw'),
    
    # Vendeurs avec géolocalisation
    path('vendors/', vendor_map_views.get_vendors_with_location, name='get_vendors_with_location'),
    path('vendors/nearby/', vendor_map_views.get_nearby_vendors, name='get_nearby_vendors'),
    path('vendors/<uuid:vendor_id>/', vendor_map_views.get_vendor_details, name='get_vendor_details'),
    
]
