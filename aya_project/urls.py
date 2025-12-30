"""
URL configuration for aya_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

def home_view(request):
    """Page d'accueil avec interface utilisateur"""
    return render(request, 'home.html')

def scan_landing_view(request):
    """Landing page pour les QR codes scannés - redirige vers les stores si l'app n'est pas installée"""
    return render(request, 'landing_page/index.html')

def privacy_policy_view(request):
    """Page de politique de confidentialité"""
    from django.utils import timezone
    context = {
        'current_date': timezone.now(),
    }
    return render(request, 'privacy_policy.html', context)

urlpatterns = [
    path('', home_view, name='home'),
    path('scan', scan_landing_view, name='scan_landing'),  # Landing page pour QR codes
    path('privacy', privacy_policy_view, name='privacy_policy'),  # Politique de confidentialité
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/vendor/', include('authentication.vendor_urls')),  # URLs spécifiques aux vendeurs
    path('api/', include('qr_codes.urls')),
    path('api/', include('dashboard.urls_api')),  # API pour publicités
    path('dashboard/', include('dashboard.urls')),
    
    # URLs d'authentification pour l'interface web
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/accounts/login/'), name='logout'),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
