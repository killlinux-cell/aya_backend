"""
Signaux Django pour la gestion automatique des tokens d'échange
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import ExchangeToken
from .tasks import cleanup_expired_tokens
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ExchangeToken)
def cleanup_expired_tokens_before_save(sender, instance, **kwargs):
    """
    Nettoie les tokens expirés avant de sauvegarder un nouveau token
    """
    try:
        # Nettoyer les tokens expirés avant de créer un nouveau
        cleanup_expired_tokens()
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage automatique: {e}")


@receiver(post_save, sender=ExchangeToken)
def log_token_creation(sender, instance, created, **kwargs):
    """
    Log la création d'un nouveau token d'échange
    """
    if created:
        logger.info(
            f"Nouveau token d'échange créé: {instance.token} "
            f"pour {instance.user.email} - {instance.points} points"
        )
