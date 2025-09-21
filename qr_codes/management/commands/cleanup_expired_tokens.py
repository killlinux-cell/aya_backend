from django.core.management.base import BaseCommand
from django.utils import timezone
from qr_codes.models import ExchangeToken
from authentication.models import User


class Command(BaseCommand):
    help = 'Nettoie les tokens d\'échange expirés et remet les points aux utilisateurs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule le nettoyage sans effectuer les modifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Trouver tous les tokens expirés et non utilisés
        expired_tokens = ExchangeToken.objects.filter(
            is_used=False,
            expires_at__lt=timezone.now()
        )
        
        expired_count = expired_tokens.count()
        
        if expired_count == 0:
            self.stdout.write(
                self.style.SUCCESS('Aucun token expiré trouvé.')
            )
            return
        
        self.stdout.write(
            f'Trouvé {expired_count} tokens expirés à nettoyer.'
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Mode simulation - aucune modification effectuée')
            )
            for token in expired_tokens:
                self.stdout.write(
                    f'Token {token.token} - Utilisateur: {token.user.email} - Points: {token.points}'
                )
            return
        
        # Traiter chaque token expiré
        processed_users = set()
        total_points_restored = 0
        
        for token in expired_tokens:
            # Utiliser la méthode du modèle pour restaurer les points
            if token.restore_user_points():
                processed_users.add(token.user.email)
                total_points_restored += token.points
                
                self.stdout.write(
                    f'Points restaurés pour {token.user.email}: +{token.points} points'
                )
        
        # Supprimer les tokens expirés
        deleted_count = expired_tokens.delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Nettoyage terminé:\n'
                f'- {deleted_count} tokens supprimés\n'
                f'- {len(processed_users)} utilisateurs concernés\n'
                f'- {total_points_restored} points restaurés au total'
            )
        )
