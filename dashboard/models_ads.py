"""
Modèles pour la gestion des publicités vidéo
"""
from django.db import models
from django.utils import timezone
import uuid


class VideoAdvertisement(models.Model):
    """
    Modèle pour gérer les vidéos publicitaires
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('scheduled', 'Programmée'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    
    # Fichier vidéo
    video_file = models.FileField(
        upload_to='advertisements/videos/',
        verbose_name="Fichier vidéo",
        help_text="Format MP4 recommandé, max 50MB"
    )
    
    # Miniature (optionnel)
    thumbnail = models.ImageField(
        upload_to='advertisements/thumbnails/',
        blank=True,
        null=True,
        verbose_name="Miniature"
    )
    
    # Paramètres d'affichage
    duration = models.IntegerField(
        default=5,
        verbose_name="Durée d'affichage (secondes)",
        help_text="Temps d'affichage avant de passer à la suivante"
    )
    priority = models.IntegerField(
        default=0,
        verbose_name="Priorité",
        help_text="Plus le nombre est élevé, plus la vidéo a de chances d'être affichée"
    )
    
    # Statut et planification
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Statut"
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de début",
        help_text="Laisser vide pour démarrer immédiatement"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de fin",
        help_text="Laisser vide pour pas de limite"
    )
    
    # Statistiques
    views_count = models.IntegerField(
        default=0,
        verbose_name="Nombre d'affichages"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ads',
        verbose_name="Créé par"
    )
    
    class Meta:
        db_table = 'video_advertisements'
        verbose_name = 'Vidéo Publicitaire'
        verbose_name_plural = 'Vidéos Publicitaires'
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.status})"
    
    def is_active_now(self):
        """Vérifie si la publicité est active maintenant"""
        if self.status != 'active':
            return False
        
        now = timezone.now()
        
        # Vérifier la date de début
        if self.start_date and now < self.start_date:
            return False
        
        # Vérifier la date de fin
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    def increment_views(self):
        """Incrémenter le compteur de vues"""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class HomeBanner(models.Model):
    """
    Bannière affichée en haut de l'écran d'accueil de l'application mobile.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Titre"
    )
    subtitle = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Sous-titre"
    )
    image = models.ImageField(
        upload_to='advertisements/banners/',
        blank=True,
        null=True,
        verbose_name="Image"
    )
    button_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Texte du bouton"
    )
    button_url = models.URLField(
        blank=True,
        verbose_name="Lien du bouton"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'home_banners'
        verbose_name = "Bannière d'accueil"
        verbose_name_plural = "Bannières d'accueil"
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or "Bannière sans titre"

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return None

