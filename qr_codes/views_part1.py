from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import date
import uuid

from .models import QRCode, UserQRCode, GameHistory, ExchangeRequest, DailyGameLimit
from .serializers import (
    QRCodeSerializer, UserQRCodeSerializer, QRCodeValidationSerializer,
    GameHistorySerializer, GamePlaySerializer, ExchangeRequestSerializer,
    ExchangeRequestCreateSerializer, ExchangeValidationSerializer,
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
