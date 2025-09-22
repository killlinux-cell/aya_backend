"""
Tâches asynchrones pour le nettoyage des tokens d'échange expirés
"""
from django.utils import timezone
from django.db import transaction
from qr_codes.models import ExchangeToken
import logging

logger = logging.getLogger(__name__)


def cleanup_expired_tokens():
    """
    Nettoie automatiquement les tokens d'échange expirés et restaure les points
    """
    try:
        # Trouver tous les tokens expirés et non utilisés
        expired_tokens = ExchangeToken.objects.filter(
            is_used=False,
            expires_at__lt=timezone.now()
        )
        
        if not expired_tokens.exists():
            logger.info("Aucun token expiré à nettoyer")
            return
        
        logger.info(f"Nettoyage de {expired_tokens.count()} tokens expirés")
        
        processed_users = set()
        total_points_restored = 0
        
        with transaction.atomic():
            for token in expired_tokens:
                # Restaurer les points de l'utilisateur
                if token.restore_user_points():
                    processed_users.add(token.user.email)
                    total_points_restored += token.points
                    
                    logger.info(
                        f"Points restaurés pour {token.user.email}: +{token.points} points"
                    )
            
            # Supprimer les tokens expirés
            deleted_count = expired_tokens.delete()[0]
            
            logger.info(
                f"Nettoyage terminé: {deleted_count} tokens supprimés, "
                f"{len(processed_users)} utilisateurs concernés, "
                f"{total_points_restored} points restaurés"
            )
            
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des tokens expirés: {e}")


def check_and_cleanup_expired_tokens():
    """
    Vérifie et nettoie les tokens expirés (à appeler périodiquement)
    """
    cleanup_expired_tokens()
