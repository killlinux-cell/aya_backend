"""
Serializers pour les publicités vidéo
"""
from rest_framework import serializers
from .models_ads import VideoAdvertisement


class VideoAdvertisementSerializer(serializers.ModelSerializer):
    """
    Serializer pour les vidéos publicitaires
    """
    video_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VideoAdvertisement
        fields = [
            'id',
            'title',
            'description',
            'video_url',
            'thumbnail_url',
            'duration',
            'priority',
            'status',
        ]
    
    def get_video_url(self, obj):
        """Retourner l'URL complète de la vidéo"""
        request = self.context.get('request')
        if obj.video_file and request:
            return request.build_absolute_uri(obj.video_file.url)
        return None
    
    def get_thumbnail_url(self, obj):
        """Retourner l'URL complète de la miniature"""
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

