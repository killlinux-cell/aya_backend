"""
Tâches asynchrones pour le nettoyage des tokens d'échange expirés
"""
from django.utils import timezone
from django.db import transaction
from qr_codes.models import ExchangeToken
from authentication.models import User
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
        
        logger.info(f"Recherche de tokens expirés...")
        logger.info(f"Tokens trouvés: {expired_tokens.count()}")
        
        if not expired_tokens.exists():
            logger.info("Aucun token expiré à nettoyer")
            return
        
        logger.info(f"Nettoyage de {expired_tokens.count()} tokens expirés")
        
        # Log des détails des tokens
        for token in expired_tokens:
            logger.info(f"Token: {token.token}, User: {token.user.email}, Points: {token.points}, Expiré: {token.expires_at}")
        
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
            
            # Restaurer les points pour chaque utilisateur en utilisant l'ORM Django
            for email, data in user_points_to_restore.items():
                user_id = data['user_id']
                points_to_restore = data['points']
                
                # Récupérer l'utilisateur et restaurer les points
                try:
                    user = User.objects.get(id=user_id)
                    user.available_points += points_to_restore
                    user.save(update_fields=['available_points'])
                    
                    processed_users.add(email)
                    total_points_restored += points_to_restore
                    
                    logger.info(
                        f"Points restaurés pour {email}: +{points_to_restore} points (nouveau total: {user.available_points})"
                    )
                except User.DoesNotExist:
                    logger.error(f"Utilisateur {email} (ID: {user_id}) non trouvé")
            
            # Marquer tous les tokens comme restaurés (ne pas les supprimer)
            ExchangeToken.objects.filter(
                id__in=token_ids_to_delete
            ).update(points_restored=True)
            
            # Compter les tokens traités (au lieu de les supprimer)
            processed_count = len(token_ids_to_delete)
            
            logger.info(
                f"Nettoyage terminé: {processed_count} tokens traités, "
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
