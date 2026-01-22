from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import User, UserProfile, PasswordResetToken, Vendor
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserUpdateSerializer, PasswordChangeSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, UserProfileExtendedSerializer,
    VendorSerializer, VendorLoginSerializer, ClientInfoSerializer
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vue personnalisée pour obtenir les tokens JWT
    """
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(APIView):
    """
    Vue pour l'inscription d'un nouvel utilisateur
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Utilisateur créé avec succès',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Vue pour récupérer et mettre à jour le profil utilisateur
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserUpdateView(generics.UpdateAPIView):
    """
    Vue pour mettre à jour les informations de base de l'utilisateur
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    """
    Vue pour changer le mot de passe
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Mot de passe modifié avec succès'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    Vue pour demander une réinitialisation de mot de passe
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email, is_active=True)
                # Créer un token de réinitialisation
                token = uuid.uuid4().hex
                expires_at = timezone.now() + timedelta(hours=1)
                
                PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )
                
                # Ici, vous pourriez envoyer un email avec le token
                # Pour la démo, on retourne le token (en production, ne pas faire ça)
                return Response({
                    'message': 'Email de réinitialisation envoyé',
                    'token': token  # À retirer en production
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # Ne pas révéler si l'email existe
                return Response({
                    'message': 'Si cet email existe, un lien de réinitialisation a été envoyé'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Vue pour confirmer la réinitialisation de mot de passe
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Mot de passe réinitialisé avec succès'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """
    Vue pour récupérer les statistiques de l'utilisateur
    """
    user = request.user
    
    # Statistiques des QR codes
    from qr_codes.models import UserQRCode
    qr_stats = UserQRCode.objects.filter(user=user)
    total_qr_scanned = qr_stats.count()
    total_points_from_qr = sum(qr.points_earned for qr in qr_stats)
    
    # Statistiques des jeux
    from qr_codes.models import GameHistory
    game_stats = GameHistory.objects.filter(user=user)
    total_games = game_stats.count()
    total_points_spent = sum(game.points_spent for game in game_stats)
    total_points_won = sum(game.points_won for game in game_stats)
    winning_games = game_stats.filter(is_winning=True).count()
    win_rate = (winning_games / total_games * 100) if total_games > 0 else 0
    
    # Statistiques des échanges
    from qr_codes.models import ExchangeRequest
    exchange_stats = ExchangeRequest.objects.filter(user=user)
    total_exchanges = exchange_stats.count()
    total_points_exchanged = sum(exchange.points for exchange in exchange_stats)
    
    # Calcul du solde actuel
    current_balance = user.available_points
    
    stats = {
        'total_qr_codes_scanned': total_qr_scanned,
        'total_points_earned_from_qr': total_points_from_qr,
        'total_games_played': total_games,
        'total_points_spent_on_games': total_points_spent,
        'total_points_won_from_games': total_points_won,
        'win_rate': round(win_rate, 2),
        'total_exchanges': total_exchanges,
        'total_points_exchanged': total_points_exchanged,
        'current_balance': current_balance,
        'total_points_earned': total_points_from_qr + total_points_won,
        'net_points_from_games': total_points_won - total_points_spent,
    }
    
    return Response(stats, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Vue pour la déconnexion (blacklist du refresh token)
    """
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({
            'message': 'Déconnexion réussie'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Token invalide'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_account(request):
    """
    Supprime définitivement le compte utilisateur et toutes ses données.
    Cette action est irréversible.
    """
    user = request.user
    
    try:
        # Importer tous les modèles nécessaires
        from qr_codes.models import (
            UserQRCode, GameHistory, ExchangeRequest, 
            DailyGameLimit, ExchangeToken
        )
        from .models_grand_prix import GrandPrixParticipation
        
        # Compter les données avant suppression (pour logging)
        qr_codes_count = UserQRCode.objects.filter(user=user).count()
        games_count = GameHistory.objects.filter(user=user).count()
        exchanges_count = ExchangeRequest.objects.filter(user=user).count()
        tokens_count = ExchangeToken.objects.filter(user=user).count()
        participations_count = GrandPrixParticipation.objects.filter(user=user).count()
        daily_limits_count = DailyGameLimit.objects.filter(user=user).count()
        
        # Supprimer toutes les données associées explicitement
        # (même si CASCADE le ferait automatiquement, on le fait pour le logging)
        
        # 1. QR codes scannés
        UserQRCode.objects.filter(user=user).delete()
        
        # 2. Historique des jeux
        GameHistory.objects.filter(user=user).delete()
        
        # 3. Demandes d'échange
        ExchangeRequest.objects.filter(user=user).delete()
        
        # 4. Tokens d'échange
        ExchangeToken.objects.filter(user=user).delete()
        
        # 5. Limites quotidiennes de jeux
        DailyGameLimit.objects.filter(user=user).delete()
        
        # 6. Participations aux grands prix
        GrandPrixParticipation.objects.filter(user=user).delete()
        
        # 7. Profil utilisateur (OneToOne, sera supprimé automatiquement avec CASCADE)
        # Mais on peut le faire explicitement
        if hasattr(user, 'profile'):
            user.profile.delete()
        
        # 8. Tokens de réinitialisation de mot de passe
        PasswordResetToken.objects.filter(user=user).delete()
        
        # 9. Vérifier si l'utilisateur est un vendeur et supprimer le profil vendeur
        if hasattr(user, 'vendor_profile'):
            user.vendor_profile.delete()
        
        # 10. Blacklister tous les tokens JWT de l'utilisateur
        # (On ne peut pas blacklister tous les tokens, mais on supprime le compte)
        
        # 11. Supprimer le compte utilisateur lui-même
        user.delete()
        
        return Response({
            'message': 'Compte supprimé avec succès',
            'deleted_data': {
                'qr_codes': qr_codes_count,
                'games': games_count,
                'exchanges': exchanges_count,
                'tokens': tokens_count,
                'grand_prix_participations': participations_count,
                'daily_limits': daily_limits_count,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Erreur lors de la suppression du compte',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VendorLoginView(APIView):
    """
    Vue pour la connexion des vendeurs
    """
    def post(self, request):
        serializer = VendorLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            vendor = serializer.validated_data['vendor']
            
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Ajouter des claims personnalisés
            access_token['vendor_id'] = str(vendor.id)
            access_token['vendor_code'] = vendor.vendor_code
            access_token['business_name'] = vendor.business_name
            
            return Response({
                'success': True,
                'access': str(access_token),
                'refresh': str(refresh),
                'vendor': VendorSerializer(vendor).data,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class VendorProfileView(APIView):
    """
    Vue pour récupérer le profil du vendeur connecté
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            vendor = Vendor.objects.get(user=request.user)
            serializer = VendorSerializer(vendor)
            return Response({
                'success': True,
                'vendor': serializer.data
            }, status=status.HTTP_200_OK)
        except Vendor.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Profil vendeur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ClientInfoView(APIView):
    """
    Vue pour récupérer les informations d'un client par son ID
    Accessible uniquement aux vendeurs authentifiés
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            # Vérifier que l'utilisateur actuel est un vendeur
            vendor = Vendor.objects.get(user=request.user)
            if not vendor.is_active:
                return Response({
                    'success': False,
                    'error': 'Compte vendeur inactif'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Récupérer les informations du client
            client = User.objects.get(id=user_id)
            serializer = ClientInfoSerializer(client)
            
            return Response({
                'success': True,
                'client': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Vendor.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Accès refusé. Compte vendeur requis.'
            }, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Client non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Erreur lors de la récupération des informations client: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VendorLoginView(APIView):
    """
    Vue pour la connexion des vendeurs
    """
    permission_classes = [permissions.AllowAny]  # Permettre l'accès sans authentification
    
    def post(self, request):
        serializer = VendorLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            try:
                # Vérifier si c'est un compte vendeur
                vendor = Vendor.objects.get(user__email=email)
                
                # Vérifier le mot de passe
                if vendor.user.check_password(password):
                    # Vérifier si le compte vendeur est actif
                    if not vendor.is_active:
                        return Response({
                            'success': False,
                            'error': 'Compte vendeur inactif'
                        }, status=status.HTTP_403_FORBIDDEN)
                    
                    # Générer les tokens JWT
                    refresh = RefreshToken.for_user(vendor.user)
                    access_token = refresh.access_token
                    
                    # Ajouter des claims personnalisés pour le vendeur
                    access_token['vendor_id'] = str(vendor.id)
                    access_token['vendor_name'] = vendor.business_name
                    access_token['is_vendor'] = True
                    
                    return Response({
                        'success': True,
                        'access': str(access_token),
                        'refresh': str(refresh),
                        'vendor': {
                            'id': str(vendor.id),
                            'business_name': vendor.business_name,
                            'vendor_code': vendor.vendor_code,
                            'contact_name': f"{vendor.user.first_name} {vendor.user.last_name}",
                            'email': vendor.user.email,
                            'status': vendor.status,
                            'is_active': vendor.status == 'active'
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'error': 'Mot de passe incorrect'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                    
            except Vendor.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Aucun compte vendeur trouvé avec cet email'
                }, status=status.HTTP_404_NOT_FOUND)
                
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_vendors(request):
    """Récupérer la liste des vendeurs disponibles"""
    try:
        print(f'🔄 available_vendors: Requête reçue de {request.user.email}')
        
        # Récupérer tous les vendeurs actifs
        vendors = Vendor.objects.filter(status='active').order_by('business_name')
        
        print(f'🏪 available_vendors: Nombre de vendeurs actifs trouvés: {vendors.count()}')
        
        vendors_data = []
        for vendor in vendors:
            print(f'   - {vendor.business_name} (ID: {vendor.id}, Status: {vendor.status})')
            vendors_data.append({
                'id': str(vendor.id),
                'business_name': vendor.business_name,
                'business_address': vendor.business_address,
                'phone_number': vendor.phone_number,
                'city': vendor.city or '',
                'region': vendor.region or '',
                'status': vendor.status,
                'latitude': vendor.latitude,
                'longitude': vendor.longitude,
            })
        
        response_data = {
            'results': vendors_data,
            'total': len(vendors_data),
        }
        
        print(f'✅ available_vendors: Réponse envoyée avec {len(vendors_data)} vendeurs')
        
        return Response(response_data)
        
    except Exception as e:
        print(f'❌ available_vendors: Erreur: {str(e)}')
        return Response({
            'error': f'Erreur lors de la récupération des vendeurs: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_vendors(request):
    """Rechercher des vendeurs par nom ou ville"""
    try:
        query = request.GET.get('q', '').strip()
        
        if not query:
            return Response({
                'results': [],
                'total': 0,
                'message': 'Terme de recherche requis'
            })
        
        from django.db.models import Q
        
        # Recherche dans le nom d'entreprise, l'adresse, la ville et la région
        vendors = Vendor.objects.filter(
            Q(business_name__icontains=query) |
            Q(business_address__icontains=query) |
            Q(city__icontains=query) |
            Q(region__icontains=query),
            status='active'
        ).order_by('business_name')
        
        vendors_data = []
        for vendor in vendors:
            vendors_data.append({
                'id': str(vendor.id),
                'business_name': vendor.business_name,
                'business_address': vendor.business_address,
                'phone_number': vendor.phone_number,
                'city': vendor.city or '',
                'region': vendor.region or '',
                'status': vendor.status,
                'latitude': vendor.latitude,
                'longitude': vendor.longitude,
            })
        
        return Response({
            'results': vendors_data,
            'total': len(vendors_data),
            'query': query,
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de la recherche de vendeurs: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def vendor_exchange_history(request):
    """Récupérer l'historique des échanges d'un vendeur"""
    try:
        print(f'🔄 vendor_exchange_history: Requête reçue de {request.user.email}')
        
        # Vérifier que l'utilisateur est un vendeur
        try:
            vendor = Vendor.objects.get(user=request.user)
            print(f'🏪 vendor_exchange_history: Vendeur trouvé: {vendor.business_name}')
        except Vendor.DoesNotExist:
            print(f'❌ vendor_exchange_history: Utilisateur {request.user.email} n\'est pas un vendeur')
            return Response({
                'error': 'Accès refusé. Compte vendeur requis.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Récupérer les échanges validés par ce vendeur (ExchangeRequest)
        from qr_codes.models import ExchangeRequest, ExchangeToken
        exchanges = ExchangeRequest.objects.filter(
            approved_by=request.user,
            status='completed'
        ).order_by('-completed_at')
        
        # Récupérer aussi les tokens d'échange utilisés (ExchangeToken)
        used_tokens = ExchangeToken.objects.filter(
            is_used=True
        ).order_by('-used_at')
        
        # Récupérer aussi les tokens d'échange en attente (pour information)
        pending_tokens = ExchangeRequest.objects.filter(
            status='pending'
        ).order_by('-created_at')[:10]  # Limiter à 10 derniers
        
        print(f'📊 vendor_exchange_history: Nombre d\'échanges validés trouvés: {exchanges.count()}')
        print(f'📋 vendor_exchange_history: Nombre de tokens utilisés trouvés: {used_tokens.count()}')
        print(f'📋 vendor_exchange_history: Nombre de tokens en attente: {pending_tokens.count()}')
        
        # Log détaillé de chaque échange validé
        for exchange in exchanges:
            print(f'   - Échange validé {exchange.id}: {exchange.points} points, {exchange.status}, approuvé par {exchange.approved_by.email}')
        
        # Log des tokens utilisés
        for token in used_tokens:
            print(f'   - Token utilisé {token.id}: {token.points} points, utilisé le {token.used_at}')
        
        # Log des tokens en attente
        for token in pending_tokens:
            print(f'   - Token en attente {token.id}: {token.points} points, créé le {token.created_at}')
        
        exchanges_data = []
        for exchange in exchanges:
            exchanges_data.append({
                'id': str(exchange.id),
                'user_id': str(exchange.user.id),
                'user_name': exchange.user.full_name,
                'user_email': exchange.user.email,
                'points': exchange.points,
                'exchange_code': exchange.exchange_code,
                'status': exchange.status,
                'created_at': exchange.created_at.isoformat(),
                'approved_at': exchange.approved_at.isoformat() if exchange.approved_at else None,
                'completed_at': exchange.completed_at.isoformat() if exchange.completed_at else None,
                'notes': exchange.notes,
                'type': 'exchange_request'
            })
        
        # Ajouter les tokens utilisés
        for token in used_tokens:
            exchanges_data.append({
                'id': str(token.id),
                'user_id': str(token.user.id),
                'user_name': token.user.full_name,
                'user_email': token.user.email,
                'points': token.points,
                'exchange_code': token.token,
                'status': 'completed',
                'created_at': token.created_at.isoformat(),
                'approved_at': token.used_at.isoformat() if token.used_at else None,
                'completed_at': token.used_at.isoformat() if token.used_at else None,
                'notes': 'Token d\'échange utilisé',
                'type': 'exchange_token'
            })
        
        # Préparer les données des tokens en attente
        pending_data = []
        for token in pending_tokens:
            pending_data.append({
                'id': str(token.id),
                'user_id': str(token.user.id),
                'user_name': token.user.full_name,
                'user_email': token.user.email,
                'points': token.points,
                'exchange_code': token.exchange_code,
                'status': token.status,
                'created_at': token.created_at.isoformat(),
                'notes': token.notes,
            })
        
        print(f'✅ vendor_exchange_history: Réponse envoyée avec {len(exchanges_data)} échanges validés (ExchangeRequest + ExchangeToken) et {len(pending_data)} tokens en attente')
        
        return Response({
            'results': exchanges_data,
            'total': len(exchanges_data),
            'pending_tokens': pending_data,
            'pending_count': len(pending_data),
            'vendor_name': vendor.business_name,
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de la récupération de l\'historique: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vendor_exchange_confirm(request):
    """Confirmer un échange côté vendeur"""
    try:
        print(f'🔄 vendor_exchange_confirm: Requête reçue de {request.user.email}')
        
        # Vérifier que l'utilisateur est un vendeur
        try:
            vendor = Vendor.objects.get(user=request.user)
            print(f'🏪 vendor_exchange_confirm: Vendeur trouvé: {vendor.business_name}')
        except Vendor.DoesNotExist:
            print(f'❌ vendor_exchange_confirm: Utilisateur {request.user.email} n\'est pas un vendeur')
            return Response({
                'error': 'Accès refusé. Compte vendeur requis.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Récupérer l'ID de l'échange
        exchange_id = request.data.get('exchange_id')
        if not exchange_id:
            return Response({
                'error': 'ID d\'échange requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Récupérer l'échange
        from qr_codes.models import ExchangeRequest
        try:
            exchange = ExchangeRequest.objects.get(id=exchange_id)
            print(f'📊 vendor_exchange_confirm: Échange trouvé: {exchange.id}, statut: {exchange.status}')
        except ExchangeRequest.DoesNotExist:
            return Response({
                'error': 'Échange non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier que l'échange peut être confirmé
        if exchange.status != 'pending':
            return Response({
                'error': f'L\'échange est déjà {exchange.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Confirmer l'échange
        exchange.status = 'completed'
        exchange.approved_by = request.user
        exchange.approved_at = timezone.now()
        exchange.completed_at = timezone.now()
        exchange.save()
        
        print(f'✅ vendor_exchange_confirm: Échange {exchange.id} confirmé avec succès')
        
        return Response({
            'success': True,
            'message': 'Échange confirmé avec succès',
            'exchange_id': str(exchange.id),
            'status': exchange.status,
        })
        
    except Exception as e:
        print(f'❌ vendor_exchange_confirm: Erreur: {str(e)}')
        return Response({
            'error': f'Erreur lors de la confirmation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)