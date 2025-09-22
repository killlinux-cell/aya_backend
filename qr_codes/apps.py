from django.apps import AppConfig


class QrCodesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'qr_codes'
    
    def ready(self):
        """Initialise les signaux lors du démarrage de l'application"""
        import qr_codes.signals