from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import date
import uuid

from .models import QRCode, UserQRCode, GameHistory, ExchangeRequest, ExchangeToken, DailyGameLimit
from .serializers import (
    QRCodeSerializer, UserQRCodeSerializer, QRCodeValidationSerializer,
    GameHistorySerializer, GamePlaySerializer, ExchangeRequestSerializer,
    ExchangeRequestCreateSerializer, ExchangeValidationSerializer,
    ExchangeTokenSerializer, ExchangeTokenCreateSerializer,
    DailyGameLimitSerializer, UserStatsSerializer
)
from authentication.models import User


class QRCodeValidationView(APIView):
    """
    Vue pour valider un QR code scanné
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = QRCodeValidationSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            user = request.user
            
            try:
                qr_code = QRCode.objects.get(code=code)
                
                # Vérifier si l'utilisateur a déjà scanné ce QR code
                if UserQRCode.objects.filter(user=user, qr_code=qr_code).exists():
                    return Response({
                        'is_valid': False,
                        'error': 'Ce QR code a déjà été scanné',
                        'error_type': 'already_used'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Créer l'association utilisateur-QR code
                user_qr_code = UserQRCode.objects.create(
                    user=user,
                    qr_code=qr_code,
                    points_earned=qr_code.points
                )
                
                # Désactiver le QR code après le premier scan
                qr_code.is_active = False
                qr_code.save(update_fields=['is_active'])
                
                # Mettre à jour les points de l'utilisateur
                user.available_points += qr_code.points
                user.collected_qr_codes += 1
                user.save(update_fields=['available_points', 'collected_qr_codes'])
                
                return Response({
                    'is_valid': True,
                    'qr_code': QRCodeSerializer(qr_code).data,
                    'points_earned': qr_code.points,
                    'message': f'Félicitations ! Vous avez gagné {qr_code.points} points !'
                }, status=status.HTTP_200_OK)
                
            except QRCode.DoesNotExist:
                return Response({
                    'is_valid': False,
                    'error': 'QR code introuvable',
                    'error_type': 'invalid_code'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QRCodeValidateAndClaimView(APIView):
    """
    Vue pour valider un QR code et réclamer le prix (avec support des tickets de fidélité)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({
                'success': False,
                'error': 'Code QR requis',
                'error_type': 'invalid_code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        try:
            qr_code = QRCode.objects.get(code=code)
            
            # Vérifier si l'utilisateur a déjà scanné ce QR code (AVANT de vérifier is_valid)
            if UserQRCode.objects.filter(user=user, qr_code=qr_code).exists():
                return Response({
                    'success': False,
                    'error': 'Ce QR code a déjà été scanné',
                    'error_type': 'already_used'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier si le QR code est valide
            if not qr_code.is_valid():
                return Response({
                    'success': False,
                    'error': 'QR code expiré ou inactif',
                    'error_type': 'expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer l'association utilisateur-QR code
            user_qr_code = UserQRCode.objects.create(
                user=user,
                qr_code=qr_code,
                points_earned=qr_code.points
            )
            
            # Désactiver le QR code après le premier scan
            qr_code.is_active = False
            qr_code.save(update_fields=['is_active'])
            
            # Mettre à jour les points de l'utilisateur (seulement pour les points, pas les tickets)
            if qr_code.prize_type == 'points':
                user.available_points += qr_code.points
                user.collected_qr_codes += 1
                user.save(update_fields=['available_points', 'collected_qr_codes'])
            
            # Préparer la réponse selon le type de prix
            if qr_code.prize_type == 'loyalty_ticket':
                message = '🎫 Félicitations ! Vous avez gagné un ticket de fidélité ! Vous pouvez maintenant jouer à un jeu !'
                prize_data = {
                    'type': 'loyalty_ticket',
                    'value': 0,
                    'description': 'Ticket de Fidélité',
                    'is_loyalty_ticket': True
                }
            else:
                message = f'🎉 Félicitations ! Vous avez gagné {qr_code.points} points !'
                prize_data = {
                    'type': 'points',
                    'value': qr_code.points,
                    'description': f'{qr_code.points} points',
                    'is_loyalty_ticket': False
                }
            
            return Response({
                'success': True,
                'qr_code': {
                    'id': str(qr_code.id),
                    'code': qr_code.code,
                    'points': qr_code.points,
                    'description': qr_code.description,
                    'is_active': qr_code.is_active,
                    'prize_type': qr_code.prize_type
                },
                'prize': prize_data,
                'message': message,
                'user_points': user.available_points,
                'qr_codes_collected': user.collected_qr_codes
            }, status=status.HTTP_200_OK)
                
        except QRCode.DoesNotExist:
            return Response({
                'success': False,
                'error': 'QR code introuvable',
                'error_type': 'invalid_code'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserQRCodesListView(generics.ListAPIView):
    """
    Vue pour lister les QR codes scannés par l'utilisateur
    """
    serializer_class = UserQRCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserQRCode.objects.filter(user=self.request.user)


class GamePlayView(APIView):
    """
    Vue pour jouer à un jeu
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = GamePlaySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            game_type = serializer.validated_data['game_type']
            points_cost = serializer.validated_data['points_cost']
            
            # Vérifier la limite quotidienne
            today = date.today()
            daily_limit, created = DailyGameLimit.objects.get_or_create(
                user=user,
                game_type=game_type,
                date=today,
                defaults={'games_played': 0}
            )
            
            if daily_limit.games_played >= 1:  # Limite d'un jeu par jour par type
                return Response({
                    'success': False,
                    'message': 'Vous avez déjà joué à ce jeu aujourd\'hui. Revenez demain !'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Générer les points gagnés (logique simplifiée)
            import random
            points_won = self._generate_game_reward(game_type)
            is_winning = points_won > 0
            
            # Créer l'historique de jeu
            game_history = GameHistory.objects.create(
                user=user,
                game_type=game_type,
                points_spent=points_cost,
                points_won=points_won,
                is_winning=is_winning
            )
            
            # Mettre à jour les points de l'utilisateur
            user.available_points = user.available_points - points_cost + points_won
            user.save(update_fields=['available_points'])
            
            # Mettre à jour la limite quotidienne
            daily_limit.games_played += 1
            daily_limit.save()
            
            # Générer le texte du prix
            prize_text = self._get_prize_text(points_won)
            
            return Response({
                'success': True,
                'points_won': points_won,
                'points_spent': points_cost,
                'net_points': points_won - points_cost,
                'is_winning': is_winning,
                'prize_text': prize_text,
                'message': f'Félicitations ! Vous avez gagné {points_won} points !' if is_winning else 'Dommage, vous n\'avez pas gagné cette fois.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _generate_game_reward(self, game_type):
        """Génère les points gagnés selon le type de jeu"""
        import random
        
        if game_type == 'scratch_and_win':
            # Scratch & Win : 0-50 points avec probabilités
            chance = random.randint(1, 100)
            if chance <= 5: return 0  # 5% de chance de rien gagner
            elif chance <= 10: return 50  # 5% de chance de 50 points
            elif chance <= 25: return 25  # 15% de chance de 25 points
            elif chance <= 45: return 15  # 20% de chance de 15 points
            elif chance <= 70: return 10  # 25% de chance de 10 points
            else: return 5  # 30% de chance de 5 points
        
        elif game_type == 'spin_wheel':
            # Roue de la chance : 0-50 points avec probabilités
            chance = random.randint(1, 100)
            if chance <= 5: return 50
            elif chance <= 15: return 25
            elif chance <= 30: return 15
            elif chance <= 55: return 10
            elif chance <= 80: return 5
            else: return 0
        
        else:
            # Jeu par défaut
            return random.randint(5, 25)
    
    def _get_prize_text(self, points):
        """Génère le texte du prix selon les points gagnés"""
        if points == 0:
            return "Rien"
        elif points == 5:
            return "5 points"
        elif points == 10:
            return "10 points"
        elif points == 15:
            return "15 points"
        elif points == 25:
            return "25 points"
        elif points == 50:
            return "50 points"
        else:
            return f"{points} points"


class GameHistoryListView(generics.ListAPIView):
    """
    Vue pour lister l'historique des jeux de l'utilisateur
    """
    serializer_class = GameHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return GameHistory.objects.filter(user=self.request.user)


class ExchangeRequestCreateView(generics.CreateAPIView):
    """
    Vue pour créer une demande d'échange
    """
    serializer_class = ExchangeRequestCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save()


class ExchangeRequestListView(generics.ListAPIView):
    """
    Vue pour lister les demandes d'échange de l'utilisateur
    """
    serializer_class = ExchangeRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ExchangeRequest.objects.filter(user=self.request.user)


class ExchangeValidationView(APIView):
    """
    Vue pour valider un code d'échange (pour les vendeurs)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ExchangeValidationSerializer(data=request.data)
        if serializer.is_valid():
            exchange_code = serializer.validated_data['exchange_code']
            
            try:
                exchange_request = ExchangeRequest.objects.get(
                    exchange_code=exchange_code,
                    status='pending'
                )
                
                return Response({
                    'is_valid': True,
                    'exchange_request': ExchangeRequestSerializer(exchange_request).data
                }, status=status.HTTP_200_OK)
                
            except ExchangeRequest.DoesNotExist:
                return Response({
                    'is_valid': False,
                    'error': 'Code d\'échange invalide ou déjà utilisé'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExchangeConfirmView(APIView):
    """
    Vue pour confirmer un échange (pour les vendeurs)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        exchange_id = request.data.get('exchange_id')
        
        if not exchange_id:
            return Response({
                'error': 'ID d\'échange requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            exchange_request = ExchangeRequest.objects.get(
                id=exchange_id,
                status='pending'
            )
            
            # Marquer comme complété
            exchange_request.status = 'completed'
            exchange_request.completed_at = timezone.now()
            exchange_request.approved_by = request.user
            exchange_request.save()
            
            return Response({
                'message': 'Échange confirmé avec succès',
                'exchange_request': ExchangeRequestSerializer(exchange_request).data
            }, status=status.HTTP_200_OK)
            
        except ExchangeRequest.DoesNotExist:
            return Response({
                'error': 'Demande d\'échange introuvable'
            }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_games(request):
    """
    Vue pour récupérer les jeux disponibles
    """
    games = [
        {
            'type': 'scratch_win',
            'name': 'Scratch & Win',
            'description': 'Grattez pour gagner des points',
            'cost': 10,
            'icon': 'brush',
            'color': 0xFFFF9800,
        },
        {
            'type': 'spin_wheel',
            'name': 'Roue de la Chance',
            'description': 'Tournez la roue pour gagner',
            'cost': 10,
            'icon': 'rotate_right',
            'color': 0xFF9C27B0,
        },
    ]
    
    return Response(games, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """
    Vue pour récupérer les statistiques détaillées de l'utilisateur
    """
    user = request.user
    
    # Statistiques des QR codes
    qr_stats = UserQRCode.objects.filter(user=user)
    total_qr_scanned = qr_stats.count()
    total_points_from_qr = sum(qr.points_earned for qr in qr_stats)
    
    # Statistiques des jeux
    game_stats = GameHistory.objects.filter(user=user)
    total_games = game_stats.count()
    total_points_spent = sum(game.points_spent for game in game_stats)
    total_points_won = sum(game.points_won for game in game_stats)
    winning_games = game_stats.filter(is_winning=True).count()
    win_rate = (winning_games / total_games * 100) if total_games > 0 else 0
    
    # Statistiques des échanges
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


class ExchangeTokenCreateView(APIView):
    """
    Vue pour créer un token d'échange temporaire
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ExchangeTokenCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                # Créer le token (cela déduit automatiquement les points)
                exchange_token = serializer.save()
                
                # Sérialiser la réponse
                token_serializer = ExchangeTokenSerializer(exchange_token)
                
                return Response({
                    'success': True,
                    'token': token_serializer.data,
                    'qr_code_data': f'EXCHANGE:{exchange_token.token}:{exchange_token.points}:{exchange_token.user.id}',
                    'expires_in_minutes': 3,
                    'message': f'Token d\'échange créé pour {exchange_token.points} points. Expire dans 3 minutes.'
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'error': f'Erreur lors de la création du token: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ExchangeTokenValidateView(APIView):
    """
    Vue pour valider et utiliser un token d'échange
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({
                'success': False,
                'error': 'Token requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Nettoyer les tokens expirés avant la validation
        from .tasks import cleanup_expired_tokens
        cleanup_expired_tokens()
        
        try:
            exchange_token = ExchangeToken.objects.get(token=token)
            
            # Vérifier si le token est valide
            if not exchange_token.is_valid:
                if exchange_token.is_expired:
                    # Restaurer les points si le token est expiré
                    if exchange_token.restore_user_points():
                        return Response({
                            'success': False,
                            'error': 'Token expiré. Vos points ont été restaurés.',
                            'points_restored': exchange_token.points
                        }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({
                            'success': False,
                            'error': 'Token expiré'
                        }, status=status.HTTP_400_BAD_REQUEST)
                elif exchange_token.is_used:
                    return Response({
                        'success': False,
                        'error': 'Token déjà utilisé'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Marquer le token comme utilisé
            exchange_token.is_used = True
            exchange_token.used_at = timezone.now()
            exchange_token.save()
            
            # Créer une demande d'échange
            exchange_request = ExchangeRequest.objects.create(
                user=exchange_token.user,
                points=exchange_token.points,
                exchange_code=token,
                status='completed',
                completed_at=timezone.now(),
                approved_by=request.user
            )
            
            # Mettre à jour les points de l'utilisateur (déjà déduits lors de la création du token)
            # Mais s'assurer que l'échange est bien comptabilisé
            user = exchange_token.user
            user.exchanged_points += exchange_token.points
            user.save(update_fields=['exchanged_points'])
            
            return Response({
                'success': True,
                'exchange_request': {
                    'id': str(exchange_request.id),
                    'user_id': str(exchange_request.user.id),
                    'user_name': exchange_request.user.full_name,
                    'user_email': exchange_request.user.email,
                    'points': exchange_request.points,
                    'exchange_code': exchange_request.exchange_code,
                    'status': exchange_request.status,
                    'created_at': exchange_request.created_at.isoformat(),
                    'approved_at': exchange_request.approved_at.isoformat() if exchange_request.approved_at else None,
                    'completed_at': exchange_request.completed_at.isoformat() if exchange_request.completed_at else None,
                    'notes': exchange_request.notes,
                },
                'message': f'Échange de {exchange_token.points} points confirmé avec succès.'
            }, status=status.HTTP_200_OK)
            
        except ExchangeToken.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Token invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Erreur lors de la validation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExchangeTokenStatusView(APIView):
    """
    Vue pour vérifier l'état des tokens d'échange de l'utilisateur
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Nettoyer les tokens expirés avant de vérifier
        from .tasks import cleanup_expired_tokens
        cleanup_expired_tokens()
        
        # Récupérer les tokens de l'utilisateur
        tokens = ExchangeToken.objects.filter(user=user).order_by('-created_at')
        
        active_tokens = []
        expired_tokens = []
        
        for token in tokens:
            if token.is_valid:
                active_tokens.append({
                    'token': token.token,
                    'points': token.points,
                    'created_at': token.created_at,
                    'expires_at': token.expires_at,
                    'is_valid': True
                })
            elif token.is_expired and not token.is_used:
                expired_tokens.append({
                    'token': token.token,
                    'points': token.points,
                    'created_at': token.created_at,
                    'expires_at': token.expires_at,
                    'is_expired': True,
                    'points_restored': token.restore_user_points()
                })
        
        return Response({
            'success': True,
            'active_tokens': active_tokens,
            'expired_tokens': expired_tokens,
            'total_active': len(active_tokens),
            'total_expired': len(expired_tokens)
        }, status=status.HTTP_200_OK)
