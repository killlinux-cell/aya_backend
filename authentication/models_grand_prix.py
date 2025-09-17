from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class GrandPrix(models.Model):
    """
    Modèle pour gérer les grands prix mensuels
    """
    STATUS_CHOICES = [
        ('upcoming', 'À venir'),
        ('active', 'En cours'),
        ('finished', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Nom du grand prix")
    description = models.TextField(verbose_name="Description")
    
    # Période du concours
    start_date = models.DateTimeField(verbose_name="Date de début")
    end_date = models.DateTimeField(verbose_name="Date de fin")
    draw_date = models.DateTimeField(verbose_name="Date de tirage au sort")
    
    # Coût de participation
    participation_cost = models.IntegerField(default=100, verbose_name="Coût de participation (points)")
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_grand_prizes')
    
    class Meta:
        db_table = 'grand_prizes'
        verbose_name = 'Grand Prix'
        verbose_name_plural = 'Grands Prix'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.status == 'active'
    
    @property
    def is_upcoming(self):
        now = timezone.now()
        return now < self.start_date and self.status == 'upcoming'
    
    @property
    def is_finished(self):
        now = timezone.now()
        return now > self.end_date or self.status == 'finished'


class GrandPrixPrize(models.Model):
    """
    Modèle pour les récompenses des grands prix
    """
    POSITION_CHOICES = [
        (1, '1er prix'),
        (2, '2ème prix'),
        (3, '3ème prix'),
        (4, '4ème prix'),
        (5, '5ème prix'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grand_prix = models.ForeignKey(GrandPrix, on_delete=models.CASCADE, related_name='prizes')
    position = models.IntegerField(choices=POSITION_CHOICES, verbose_name="Position")
    name = models.CharField(max_length=200, verbose_name="Nom de la récompense")
    description = models.TextField(verbose_name="Description")
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valeur (€)")
    
    class Meta:
        db_table = 'grand_prize_prizes'
        verbose_name = 'Récompense Grand Prix'
        verbose_name_plural = 'Récompenses Grand Prix'
        ordering = ['position']
        unique_together = ['grand_prix', 'position']
    
    def __str__(self):
        return f"{self.get_position_display()} - {self.name}"


class GrandPrixParticipation(models.Model):
    """
    Modèle pour les participations au grand prix
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grand_prix = models.ForeignKey(GrandPrix, on_delete=models.CASCADE, related_name='participations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grand_prix_participations')
    
    # Coût de participation
    points_spent = models.IntegerField(verbose_name="Points dépensés")
    
    # Statut de la participation
    is_winner = models.BooleanField(default=False, verbose_name="Gagnant")
    prize_won = models.ForeignKey(GrandPrixPrize, on_delete=models.SET_NULL, null=True, blank=True, related_name='winners')
    
    # Métadonnées
    participated_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de participation")
    notified_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de notification")
    
    class Meta:
        db_table = 'grand_prize_participations'
        verbose_name = 'Participation Grand Prix'
        verbose_name_plural = 'Participations Grand Prix'
        ordering = ['-participated_at']
        unique_together = ['grand_prix', 'user']  # Un utilisateur ne peut participer qu'une fois par grand prix
    
    def __str__(self):
        return f"{self.user.email} - {self.grand_prix.name}"
    
    @property
    def is_eligible_for_draw(self):
        return not self.is_winner and self.grand_prix.is_finished


class GrandPrixDraw(models.Model):
    """
    Modèle pour les tirages au sort des grands prix
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grand_prix = models.ForeignKey(GrandPrix, on_delete=models.CASCADE, related_name='draws')
    
    # Résultats du tirage
    winners = models.ManyToManyField(GrandPrixParticipation, related_name='draw_wins', blank=True)
    
    # Métadonnées
    drawn_at = models.DateTimeField(auto_now_add=True, verbose_name="Date du tirage")
    drawn_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducted_draws')
    
    class Meta:
        db_table = 'grand_prize_draws'
        verbose_name = 'Tirage Grand Prix'
        verbose_name_plural = 'Tirages Grand Prix'
        ordering = ['-drawn_at']
    
    def __str__(self):
        return f"Tirage {self.grand_prix.name} - {self.drawn_at.strftime('%d/%m/%Y %H:%M')}"
