from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailBackend(ModelBackend):
    """
    Backend d'authentification personnalisé pour utiliser l'email au lieu du nom d'utilisateur
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Chercher l'utilisateur par email
            user = User.objects.get(Q(email__iexact=username) | Q(username__iexact=username))
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
