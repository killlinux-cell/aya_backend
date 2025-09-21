from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

User = get_user_model()


class QRCode(models.Model):
    """
    Modèle pour les QR codes du système
    """
    PRIZE_TYPES = [
        ('points', 'Points'),
        ('try_again', 'Réessayer'),
        ('loyalty_bonus', 'Bonus Fidélité'),
        ('mystery_box', 'Boîte Mystère'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True)
    points = models.IntegerField()
    description = models.TextField(max_length=500)
    prize_type = models.CharField(max_length=20, choices=PRIZE_TYPES, default='points')
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_qr_codes')
    
    # Gestion des lots
    batch_number = models.CharField(max_length=50, blank=True, help_text="Numéro de lot (ex: 4151000)")
    batch_sequence = models.IntegerField(null=True, blank=True, help_text="Numéro de séquence dans le lot")
    is_printed = models.BooleanField(default=False, help_text="QR code imprimé sur bouteille")
    
    class Meta:
        db_table = 'qr_codes'
        verbose_name = 'QR Code'
        verbose_name_plural = 'QR Codes'
        ordering = ['-created_at']
    
    def __str__(self):
        prize_display = self.get_prize_type_display()
        if self.prize_type == 'loyalty_ticket':
            return f"QR Code: {self.code} (Ticket de Fidélité)"
        else:
            return f"QR Code: {self.code} ({self.points} points - {prize_display})"
    
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return self.is_active and not self.is_expired()


class UserQRCode(models.Model):
    """
    Association entre utilisateur et QR code scanné
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scanned_qr_codes')
    qr_code = models.ForeignKey(QRCode, on_delete=models.CASCADE, related_name='scanned_by_users')
    scanned_at = models.DateTimeField(auto_now_add=True)
    points_earned = models.IntegerField()
    
    class Meta:
        db_table = 'user_qr_codes'
        verbose_name = 'User QR Code'
        verbose_name_plural = 'User QR Codes'
        unique_together = ['user', 'qr_code']  # Un utilisateur ne peut scanner un QR code qu'une fois
        ordering = ['-scanned_at']
    
    def __str__(self):
        return f"{self.user.full_name} scanned {self.qr_code.code}"


class GameHistory(models.Model):
    """
    Historique des jeux joués par les utilisateurs
    """
    GAME_TYPES = [
        ('scratch_win', 'Scratch & Win'),
        ('spin_wheel', 'Roue de la Chance'),
        ('memory_game', 'Jeu de Mémoire'),
        ('quiz', 'Quiz'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_history')
    game_type = models.CharField(max_length=20, choices=GAME_TYPES)
    points_spent = models.IntegerField()
    points_won = models.IntegerField()
    played_at = models.DateTimeField(auto_now_add=True)
    is_winning = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'game_history'
        verbose_name = 'Game History'
        verbose_name_plural = 'Game History'
        ordering = ['-played_at']
    
    def __str__(self):
        return f"{self.user.full_name} played {self.get_game_type_display()} - {self.points_won} points won"


class ExchangeRequest(models.Model):
    """
    Demandes d'échange de points
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('completed', 'Complété'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exchange_requests')
    points = models.IntegerField()
    exchange_code = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_exchanges')
    notes = models.TextField(max_length=500, blank=True)
    
    class Meta:
        db_table = 'exchange_requests'
        verbose_name = 'Exchange Request'
        verbose_name_plural = 'Exchange Requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Exchange request from {self.user.full_name} - {self.points} points"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def formatted_date(self):
        return self.created_at.strftime('%d/%m/%Y à %H:%M')


class DailyGameLimit(models.Model):
    """
    Limites quotidiennes de jeux par utilisateur
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_game_limits')
    game_type = models.CharField(max_length=20, choices=GameHistory.GAME_TYPES)
    date = models.DateField()
    games_played = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'daily_game_limits'
        verbose_name = 'Daily Game Limit'
        verbose_name_plural = 'Daily Game Limits'
        unique_together = ['user', 'game_type', 'date']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_game_type_display()} on {self.date}"


class ExchangeToken(models.Model):
    """
    Tokens d'échange temporaires avec expiration
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exchange_tokens')
    points = models.IntegerField()
    token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'exchange_tokens'
        verbose_name = 'Exchange Token'
        verbose_name_plural = 'Exchange Tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Exchange token for {self.user.full_name} - {self.points} points"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
    
    def restore_user_points(self):
        """
        Restaure les points de l'utilisateur si le token expire sans être utilisé
        """
        if not self.is_used and self.is_expired:
            self.user.available_points += self.points
            self.user.save(update_fields=['available_points'])
            return True
        return False