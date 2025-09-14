from django.urls import path
from django.http import JsonResponse
from . import views

def api_root(request):
    """Vue racine de l'API qui retourne les endpoints disponibles"""
    return JsonResponse({
        'message': 'Aya+ API v1.0.0',
        'endpoints': {
            'authentication': '/api/auth/',
            'qr_codes': '/api/validate/',
            'games': '/api/games/',
            'exchanges': '/api/exchanges/',
            'stats': '/api/stats/',
        },
        'documentation': 'https://aya-plus.orapide.shop'
    })

urlpatterns = [
    # Vue racine de l'API
    path('', api_root, name='api_root'),
    # QR Codes
    path('validate/', views.QRCodeValidationView.as_view(), name='qr_validate'),
    path('validate-and-claim/', views.QRCodeValidateAndClaimView.as_view(), name='qr_validate_and_claim'),
    path('user-codes/', views.UserQRCodesListView.as_view(), name='user_qr_codes'),
    
    # Jeux
    path('games/play/', views.GamePlayView.as_view(), name='game_play'),
    path('games/history/', views.GameHistoryListView.as_view(), name='game_history'),
    path('games/available/', views.available_games, name='available_games'),
    
    # Échanges
    path('exchanges/create/', views.ExchangeRequestCreateView.as_view(), name='exchange_create'),
    path('exchanges/list/', views.ExchangeRequestListView.as_view(), name='exchange_list'),
    path('exchanges/validate/', views.ExchangeValidationView.as_view(), name='exchange_validate'),
    path('exchanges/confirm/', views.ExchangeConfirmView.as_view(), name='exchange_confirm'),
    
    # Tokens d'échange temporaires
    path('exchange-tokens/create/', views.ExchangeTokenCreateView.as_view(), name='exchange_token_create'),
    path('exchange-tokens/validate/', views.ExchangeTokenValidateView.as_view(), name='exchange_token_validate'),
    
    # Statistiques
    path('stats/', views.user_stats, name='qr_user_stats'),
]
