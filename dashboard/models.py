from django.db import models
from django.contrib.auth import get_user_model
from qr_codes.models import QRCode
import uuid

User = get_user_model()

class MysteryBoxHistory(models.Model):
    """Historique des Mystery Box ouvertes par les utilisateurs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mystery_box_history')
    qr_code = models.ForeignKey(QRCode, on_delete=models.CASCADE)
    prize_type = models.CharField(max_length=50)
    prize_value = models.IntegerField(default=0)
    prize_description = models.TextField(max_length=200)
    is_special_prize = models.BooleanField(default=False)
    opened_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-opened_at']
        verbose_name = 'Mystery Box History'
        verbose_name_plural = 'Mystery Box Histories'
    
    def __str__(self):
        return f"{self.user.email} - {self.prize_description} ({self.opened_at.strftime('%Y-%m-%d %H:%M')})"
