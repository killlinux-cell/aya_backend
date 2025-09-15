from rest_framework import serializers
from .models import QRCode, UserQRCode, GameHistory, ExchangeRequest, ExchangeToken, DailyGameLimit
from authentication.models import User


class QRCodeSerializer(serializers.ModelSerializer):
    """
    Serializer pour les QR codes
    """
    is_valid = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = QRCode
        fields = (
            'id', 'code', 'points', 'description', 'is_active',
            'expires_at', 'is_valid', 'is_expired', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class UserQRCodeSerializer(serializers.ModelSerializer):
    """
    Serializer pour les QR codes scannés par l'utilisateur
    """
    qr_code = QRCodeSerializer(read_only=True)
    qr_code_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = UserQRCode
        fields = (
            'id', 'qr_code', 'qr_code_id', 'scanned_at', 'points_earned'
        )
        read_only_fields = ('id', 'scanned_at', 'points_earned')


class QRCodeValidationSerializer(serializers.Serializer):
    """
    Serializer pour la validation d'un QR code
    """
    code = serializers.CharField(max_length=100)
    
    def validate_code(self, value):
        try:
            qr_code = QRCode.objects.get(code=value)
            if not qr_code.is_valid():
                raise serializers.ValidationError('Ce QR code n\'est plus valide ou a expiré.')
        except QRCode.DoesNotExist:
            raise serializers.ValidationError('QR code introuvable.')
        return value


class GameHistorySerializer(serializers.ModelSerializer):
    """
    Serializer pour l'historique des jeux
    """
    game_type_display = serializers.CharField(source='get_game_type_display', read_only=True)
    
    class Meta:
        model = GameHistory
        fields = (
            'id', 'game_type', 'game_type_display', 'points_spent',
            'points_won', 'played_at', 'is_winning'
        )
        read_only_fields = ('id', 'played_at', 'is_winning')


class GamePlaySerializer(serializers.Serializer):
    """
    Serializer pour jouer à un jeu
    """
    game_type = serializers.ChoiceField(choices=GameHistory.GAME_TYPES)
    points_cost = serializers.IntegerField(min_value=1)
    
    def validate_points_cost(self, value):
        user = self.context['request'].user
        if user.available_points < value:
            raise serializers.ValidationError('Points insuffisants.')
        return value


class ExchangeRequestSerializer(serializers.ModelSerializer):
    """
    Serializer pour les demandes d'échange
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_completed = serializers.ReadOnlyField()
    formatted_date = serializers.ReadOnlyField()
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = ExchangeRequest
        fields = (
            'id', 'user', 'user_name', 'points', 'exchange_code', 'status',
            'status_display', 'is_completed', 'formatted_date', 'created_at',
            'approved_at', 'completed_at', 'notes'
        )
        read_only_fields = (
            'id', 'user', 'exchange_code', 'status', 'created_at',
            'approved_at', 'completed_at'
        )


class ExchangeRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer une demande d'échange
    """
    class Meta:
        model = ExchangeRequest
        fields = ('points',)
    
    def validate_points(self, value):
        user = self.context['request'].user
        if value <= 0:
            raise serializers.ValidationError('Le nombre de points doit être positif.')
        if user.available_points < value:
            raise serializers.ValidationError('Points insuffisants.')
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        exchange_code = f"EXCH_{user.id.hex[:8].upper()}_{int(timezone.now().timestamp())}"
        
        exchange_request = ExchangeRequest.objects.create(
            user=user,
            exchange_code=exchange_code,
            **validated_data
        )
        
        # Déduire les points de l'utilisateur
        user.available_points -= validated_data['points']
        user.exchanged_points += validated_data['points']
        user.save(update_fields=['available_points', 'exchanged_points'])
        
        return exchange_request




class ExchangeTokenSerializer(serializers.ModelSerializer):
    """
    Serializer pour les tokens d'échange temporaires
    """
    is_valid = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = ExchangeToken
        fields = [
            'id', 'points', 'token', 'expires_at', 
            'is_used', 'used_at', 'created_at',
            'is_valid', 'is_expired'
        ]
        read_only_fields = ['id', 'token', 'created_at', 'is_used', 'used_at']


class ExchangeTokenCreateSerializer(serializers.Serializer):
    """
    Serializer pour créer un token d'échange
    """
    points = serializers.IntegerField(min_value=1, max_value=10000)
    
    def validate_points(self, value):
        user = self.context['request'].user
        if user.available_points < value:
            raise serializers.ValidationError(
                f"Points insuffisants. Vous avez {user.available_points} points disponibles."
            )
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        points = validated_data['points']
        
        # Déduire les points de l'utilisateur immédiatement
        user.available_points -= points
        user.save(update_fields=['available_points'])
        
        # Générer un token unique
        import secrets
        import string
        from django.utils import timezone
        
        token = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        expires_at = timezone.now() + timezone.timedelta(minutes=3)
        
        exchange_token = ExchangeToken.objects.create(
            user=user,
            points=points,
            token=token,
            expires_at=expires_at
        )
        
        return exchange_token


class ExchangeValidationSerializer(serializers.Serializer):
    """
    Serializer pour valider un code d'échange
    """
    exchange_code = serializers.CharField(max_length=50)
    
    def validate_exchange_code(self, value):
        try:
            exchange_request = ExchangeRequest.objects.get(
                exchange_code=value,
                status='pending'
            )
        except ExchangeRequest.DoesNotExist:
            raise serializers.ValidationError('Code d\'échange invalide ou déjà utilisé.')
        return value


class DailyGameLimitSerializer(serializers.ModelSerializer):
    """
    Serializer pour les limites quotidiennes de jeux
    """
    game_type_display = serializers.CharField(source='get_game_type_display', read_only=True)
    
    class Meta:
        model = DailyGameLimit
        fields = (
            'user', 'game_type', 'game_type_display', 'date', 'games_played'
        )
        read_only_fields = ('user', 'date')


class UserStatsSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques utilisateur
    """
    total_qr_codes_scanned = serializers.IntegerField()
    total_points_earned = serializers.IntegerField()
    total_games_played = serializers.IntegerField()
    total_points_spent_on_games = serializers.IntegerField()
    total_points_won_from_games = serializers.IntegerField()
    total_exchanges = serializers.IntegerField()
    total_points_exchanged = serializers.IntegerField()
    win_rate = serializers.FloatField()
    current_balance = serializers.IntegerField()
