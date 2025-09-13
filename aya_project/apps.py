from django.apps import AppConfig
from django.contrib import admin

class AyaProjectConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aya_project'
    
    def ready(self):
        # Configuration de l'admin Django
        admin.site.site_header = "Administration Aya"
        admin.site.site_title = "Aya Admin"
        admin.site.index_title = "Tableau de bord Aya"
