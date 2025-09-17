from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from .models import User
from .models_grand_prix import GrandPrix, GrandPrixParticipation, GrandPrixPrize
import random


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_grand_prix(request):
    """Récupérer le grand prix actuel"""
    try:
        now = timezone.now()
        
        # Chercher un grand prix actif
        grand_prix = GrandPrix.objects.filter(
            start_date__lte=now,
            end_date__gte=now,
            status='active'
        ).first()
        
        if not grand_prix:
            return Response({
                'error': 'Aucun grand prix actif actuellement'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier si l'utilisateur a déjà participé
        has_participated = GrandPrixParticipation.objects.filter(
            grand_prix=grand_prix,
            user=request.user
        ).exists()
        
        # Récupérer les récompenses
        prizes = GrandPrixPrize.objects.filter(grand_prix=grand_prix).order_by('position')
        
        return Response({
            'success': True,
            'grand_prix': {
                'id': str(grand_prix.id),
                'name': grand_prix.name,
                'description': grand_prix.description,
                'participation_cost': grand_prix.participation_cost,
                'start_date': grand_prix.start_date.isoformat(),
                'end_date': grand_prix.end_date.isoformat(),
                'draw_date': grand_prix.draw_date.isoformat(),
                'has_participated': has_participated,
                'prizes': [
                    {
                        'position': prize.position,
                        'name': prize.name,
                        'description': prize.description,
                        'value': float(prize.value) if prize.value else None,
                    }
                    for prize in prizes
                ]
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de la récupération du grand prix: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def participate_in_grand_prix(request):
    """Participer au grand prix actuel"""
    try:
        now = timezone.now()
        
        # Chercher un grand prix actif
        grand_prix = GrandPrix.objects.filter(
            start_date__lte=now,
            end_date__gte=now,
            status='active'
        ).first()
        
        if not grand_prix:
            return Response({
                'error': 'Aucun grand prix actif actuellement'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier si l'utilisateur a déjà participé
        if GrandPrixParticipation.objects.filter(
            grand_prix=grand_prix,
            user=request.user
        ).exists():
            return Response({
                'error': 'Vous avez déjà participé à ce grand prix'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si l'utilisateur a assez de points
        if request.user.available_points < grand_prix.participation_cost:
            return Response({
                'error': f'Points insuffisants. Coût de participation: {grand_prix.participation_cost} points'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier le statut VIP (100+ points)
        if request.user.available_points < 100:
            return Response({
                'error': 'Statut VIP requis (100+ points) pour participer au grand prix'
            }, status=status.HTTP_403_FORBIDDEN)
        
        with transaction.atomic():
            # Retirer les points de l'utilisateur
            request.user.available_points -= grand_prix.participation_cost
            request.user.save()
            
            # Créer la participation
            participation = GrandPrixParticipation.objects.create(
                grand_prix=grand_prix,
                user=request.user,
                points_spent=grand_prix.participation_cost
            )
            
            print(f'✅ Participation créée: {request.user.email} - {grand_prix.name} - {grand_prix.participation_cost} points')
        
        return Response({
            'success': True,
            'message': 'Participation enregistrée avec succès !',
            'participation': {
                'id': str(participation.id),
                'grand_prix_name': grand_prix.name,
                'points_spent': grand_prix.participation_cost,
                'participated_at': participation.participated_at.isoformat(),
            },
            'user_points': request.user.available_points
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de la participation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_participations(request):
    """Récupérer les participations de l'utilisateur"""
    try:
        participations = GrandPrixParticipation.objects.filter(
            user=request.user
        ).select_related('grand_prix', 'prize_won').order_by('-participated_at')
        
        return Response({
            'success': True,
            'participations': [
                {
                    'id': str(participation.id),
                    'grand_prix_name': participation.grand_prix.name,
                    'points_spent': participation.points_spent,
                    'is_winner': participation.is_winner,
                    'prize_won': {
                        'name': participation.prize_won.name,
                        'position': participation.prize_won.position,
                        'description': participation.prize_won.description,
                    } if participation.prize_won else None,
                    'participated_at': participation.participated_at.isoformat(),
                    'notified_at': participation.notified_at.isoformat() if participation.notified_at else None,
                }
                for participation in participations
            ]
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de la récupération des participations: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_grand_prix_participants(request, grand_prix_id):
    """Récupérer la liste des participants d'un grand prix (admin seulement)"""
    try:
        # Vérifier que l'utilisateur est admin
        if not request.user.is_staff:
            return Response({
                'error': 'Accès refusé. Droits administrateur requis.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            grand_prix = GrandPrix.objects.get(id=grand_prix_id)
        except GrandPrix.DoesNotExist:
            return Response({
                'error': 'Grand prix non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        participants = GrandPrixParticipation.objects.filter(
            grand_prix=grand_prix
        ).select_related('user').order_by('-participated_at')
        
        return Response({
            'success': True,
            'grand_prix': {
                'id': str(grand_prix.id),
                'name': grand_prix.name,
                'status': grand_prix.status,
                'total_participants': participants.count(),
            },
            'participants': [
                {
                    'id': str(participation.id),
                    'user_email': participation.user.email,
                    'user_name': participation.user.full_name,
                    'points_spent': participation.points_spent,
                    'is_winner': participation.is_winner,
                    'prize_won': participation.prize_won.name if participation.prize_won else None,
                    'participated_at': participation.participated_at.isoformat(),
                }
                for participation in participants
            ]
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de la récupération des participants: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def conduct_grand_prix_draw(request, grand_prix_id):
    """Effectuer le tirage au sort d'un grand prix (admin seulement)"""
    try:
        # Vérifier que l'utilisateur est admin
        if not request.user.is_staff:
            return Response({
                'error': 'Accès refusé. Droits administrateur requis.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            grand_prix = GrandPrix.objects.get(id=grand_prix_id)
        except GrandPrix.DoesNotExist:
            return Response({
                'error': 'Grand prix non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier que le grand prix est terminé
        if not grand_prix.is_finished:
            return Response({
                'error': 'Le grand prix n\'est pas encore terminé'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier qu'il n'y a pas déjà eu de tirage
        if hasattr(grand_prix, 'draws') and grand_prix.draws.exists():
            return Response({
                'error': 'Le tirage au sort a déjà été effectué pour ce grand prix'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Récupérer tous les participants éligibles
            participants = list(GrandPrixParticipation.objects.filter(
                grand_prix=grand_prix,
                is_winner=False
            ))
            
            if not participants:
                return Response({
                    'error': 'Aucun participant éligible pour le tirage'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer les récompenses disponibles
            prizes = list(GrandPrixPrize.objects.filter(grand_prix=grand_prix).order_by('position'))
            
            if not prizes:
                return Response({
                    'error': 'Aucune récompense définie pour ce grand prix'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Effectuer le tirage au sort
            winners = []
            for prize in prizes:
                if participants:  # S'il reste des participants
                    winner = random.choice(participants)
                    participants.remove(winner)  # Retirer le gagnant de la liste
                    
                    # Marquer comme gagnant
                    winner.is_winner = True
                    winner.prize_won = prize
                    winner.save()
                    
                    winners.append({
                        'position': prize.position,
                        'prize_name': prize.name,
                        'winner_email': winner.user.email,
                        'winner_name': winner.user.full_name,
                    })
            
            # Créer l'enregistrement du tirage
            from .models_grand_prix import GrandPrixDraw
            draw = GrandPrixDraw.objects.create(
                grand_prix=grand_prix,
                drawn_by=request.user
            )
            draw.winners.set([p for p in GrandPrixParticipation.objects.filter(
                grand_prix=grand_prix,
                is_winner=True
            )])
            
            print(f'✅ Tirage au sort effectué: {grand_prix.name} - {len(winners)} gagnant(s)')
        
        return Response({
            'success': True,
            'message': 'Tirage au sort effectué avec succès !',
            'winners': winners,
            'total_participants': len(participants) + len(winners),
            'total_winners': len(winners)
        })
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors du tirage au sort: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
