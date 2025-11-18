"""
Vues pour la gestion des publicités vidéo
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from .models_ads import VideoAdvertisement, HomeBanner
from .serializers_ads import VideoAdvertisementSerializer
import random


def is_admin(user):
    """Vérifier si l'utilisateur est admin"""
    return user.is_staff or user.is_superuser


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def active_advertisements(request):
    """
    API pour récupérer les vidéos publicitaires actives
    Endpoint : /api/advertisements/active/
    """
    # Récupérer toutes les vidéos actives
    ads = VideoAdvertisement.objects.filter(status='active')
    
    # Filtrer par date si applicable
    active_ads = [ad for ad in ads if ad.is_active_now()]
    
    # Sérialiser avec le contexte de la requête pour les URLs complètes
    serializer = VideoAdvertisementSerializer(
        active_ads,
        many=True,
        context={'request': request}
    )
    
    return Response({
        'count': len(active_ads),
        'advertisements': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def increment_view(request, ad_id):
    """
    Incrémenter le compteur de vues d'une publicité
    Endpoint : /api/advertisements/{ad_id}/view/
    """
    try:
        ad = VideoAdvertisement.objects.get(id=ad_id)
        ad.increment_views()
        return Response({'success': True, 'views': ad.views_count})
    except VideoAdvertisement.DoesNotExist:
        return Response(
            {'error': 'Publicité non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )


@login_required
@user_passes_test(is_admin)
def advertisements_management(request):
    """
    Page de gestion des publicités vidéo dans le dashboard
    """
    search = request.GET.get('search', '')
    ads = VideoAdvertisement.objects.all()
    
    if search:
        ads = ads.filter(title__icontains=search)
    
    # Pagination
    paginator = Paginator(ads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': VideoAdvertisement.objects.count(),
        'active': VideoAdvertisement.objects.filter(status='active').count(),
        'inactive': VideoAdvertisement.objects.filter(status='inactive').count(),
        'total_views': sum(ad.views_count for ad in VideoAdvertisement.objects.all()),
    }
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'stats': stats,
    }
    
    return render(request, 'dashboard/advertisements.html', context)


@login_required
@user_passes_test(is_admin)
def create_advertisement(request):
    """
    Créer une nouvelle publicité vidéo
    """
    if request.method == 'POST':
        try:
            ad = VideoAdvertisement.objects.create(
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                video_file=request.FILES.get('video_file'),
                thumbnail=request.FILES.get('thumbnail'),
                duration=int(request.POST.get('duration', 5)),
                priority=int(request.POST.get('priority', 0)),
                status=request.POST.get('status', 'active'),
                created_by=request.user,
            )
            
            messages.success(request, f'Publicité "{ad.title}" créée avec succès !')
            return redirect('dashboard:advertisements')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {e}')
    
    return render(request, 'dashboard/create_advertisement.html')


@login_required
@user_passes_test(is_admin)
def delete_advertisement(request, ad_id):
    """
    Supprimer une publicité vidéo
    """
    try:
        ad = VideoAdvertisement.objects.get(id=ad_id)
        ad.delete()
        messages.success(request, 'Publicité supprimée avec succès !')
    except VideoAdvertisement.DoesNotExist:
        messages.error(request, 'Publicité introuvable')
    
    return redirect('dashboard:advertisements')


@login_required
@user_passes_test(is_admin)
def home_banner_settings(request):
    """
    Page de gestion de la bannière d'accueil (image affichée au-dessus de "Mes Points").
    """
    banner = HomeBanner.objects.first()

    if not banner:
        banner = HomeBanner.objects.create(
            title="Aya+",
            subtitle="Fidélisez vos clients avec style",
            button_text="Découvrir Aya+",
            button_url="https://example.com",
        )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'reset_image':
            if banner.image:
                banner.image.delete(save=False)
                banner.image = None
                banner.save(update_fields=['image', 'updated_at'])
                messages.success(request, "Image réinitialisée avec succès.")
            else:
                messages.info(request, "Aucune image à réinitialiser.")
            return redirect('dashboard:home_banner')

        banner.title = request.POST.get('title', '').strip()
        banner.subtitle = request.POST.get('subtitle', '').strip()
        banner.button_text = request.POST.get('button_text', '').strip()
        banner.button_url = request.POST.get('button_url', '').strip()
        banner.is_active = request.POST.get('is_active') == 'on'

        if request.FILES.get('image'):
            banner.image = request.FILES['image']

        banner.save()
        messages.success(request, "Bannière mise à jour avec succès.")
        return redirect('dashboard:home_banner')

    context = {
        'banner': banner
    }
    return render(request, 'dashboard/home_banner.html', context)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def home_banner_details(request):
    """
    API pour récupérer la bannière active affichée dans l'application mobile.
    Endpoint : /api/advertisements/banner/
    """
    banner = HomeBanner.objects.filter(is_active=True).order_by('-updated_at').first()

    if not banner:
        return Response({'banner': None})

    banner_data = {
        'id': str(banner.id),
        'title': banner.title,
        'subtitle': banner.subtitle,
        'button_text': banner.button_text,
        'button_url': banner.button_url,
        'image_url': request.build_absolute_uri(banner.image.url) if banner.image else None,
        'updated_at': banner.updated_at.isoformat(),
    }

    return Response({'banner': banner_data})


@login_required
@user_passes_test(is_admin)
def toggle_advertisement_status(request, ad_id):
    """
    Activer/désactiver une publicité
    """
    try:
        ad = VideoAdvertisement.objects.get(id=ad_id)
        ad.status = 'inactive' if ad.status == 'active' else 'active'
        ad.save()
        messages.success(request, f'Publicité "{ad.title}" {ad.status} !')
    except VideoAdvertisement.DoesNotExist:
        messages.error(request, 'Publicité introuvable')
    
    return redirect('dashboard:advertisements')

