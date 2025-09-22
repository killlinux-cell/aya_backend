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
        # Trouver tous les tokens expirés et non utilisés qui n'ont pas encore été restaurés
        expired_tokens = ExchangeToken.objects.filter(
            is_used=False,
            expires_at__lt=timezone.now(),
            points_restored=False
        )
        
        if not expired_tokens.exists():
            logger.info("Aucun token expiré à nettoyer")
            return
        
        logger.info(f"Nettoyage de {expired_tokens.count()} tokens expirés")
        
        processed_users = set()
        total_points_restored = 0
        
        with transaction.atomic():
            # Grouper les tokens par utilisateur pour optimiser les mises à jour
            user_points_to_restore = {}
            token_ids_to_delete = []
            
            for token in expired_tokens:
                if token.user.email not in user_points_to_restore:
                    user_points_to_restore[token.user.email] = {
                        'user_id': token.user.id,
                        'points': 0
                    }
                
                user_points_to_restore[token.user.email]['points'] += token.points
                token_ids_to_delete.append(token.id)
            
            # Restaurer les points pour chaque utilisateur en utilisant des requêtes SQL directes
            from django.db import connection
            
            for email, data in user_points_to_restore.items():
                user_id = data['user_id']
                points_to_restore = data['points']
                
                # Mettre à jour les points de l'utilisateur avec une requête SQL directe
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE auth_user SET available_points = available_points + %s WHERE id = %s",
                        [points_to_restore, str(user_id)]
                    )
                
                # Marquer tous les tokens de cet utilisateur comme restaurés
                ExchangeToken.objects.filter(
                    user_id=user_id,
                    id__in=token_ids_to_delete
                ).update(points_restored=True)
                
                processed_users.add(email)
                total_points_restored += points_to_restore
                
                logger.info(
                    f"Points restaurés pour {email}: +{points_to_restore} points"
                )
            
            # Supprimer les tokens expirés
            deleted_count = ExchangeToken.objects.filter(
                id__in=token_ids_to_delete
            ).delete()[0]
            
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
