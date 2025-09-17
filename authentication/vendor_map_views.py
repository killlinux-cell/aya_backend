from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Vendor
from django.core.paginator import Paginator
import json

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_vendors_with_location(request):
    """Récupérer la liste des vendeurs avec leurs positions GPS"""
    try:
        print(f'🔄 get_vendors_with_location: Requête reçue de {request.user.email}')
        
        # Récupérer les paramètres de pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        
        # Récupérer les vendeurs actifs avec coordonnées GPS
        vendors = Vendor.objects.filter(
            status='active',
            latitude__isnull=False,
            longitude__isnull=False,
        ).exclude(
            latitude=0,
            longitude=0,
        ).select_related('user')
        
        # Pagination
        paginator = Paginator(vendors, page_size)
        page_obj = paginator.get_page(page)
        
        # Construire la réponse
        vendors_data = []
        for vendor in page_obj:
            vendor_data = {
                'id': str(vendor.id),
                'business_name': vendor.business_name,
                'vendor_code': vendor.vendor_code,
                'business_address': vendor.business_address,
                'phone_number': vendor.phone_number,
                'latitude': float(vendor.latitude) if vendor.latitude else 0.0,
                'longitude': float(vendor.longitude) if vendor.longitude else 0.0,
                'city': vendor.city,
                'region': vendor.region,
                'country': vendor.country,
                'status': vendor.status,
                'user_email': vendor.user.email,
                'user_name': f"{vendor.user.first_name} {vendor.user.last_name}".strip(),
            }
            vendors_data.append(vendor_data)
        
        response_data = {
            'success': True,
            'count': paginator.count,
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'results': vendors_data,
        }
        
        print(f'✅ get_vendors_with_location: {len(vendors_data)} vendeurs retournés')
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f'❌ get_vendors_with_location: Erreur: {str(e)}')
        return Response({
            'success': False,
            'error': f'Erreur lors de la récupération des vendeurs: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nearby_vendors(request):
    """Récupérer les vendeurs proches d'une position donnée"""
    try:
        print(f'🔄 get_nearby_vendors: Requête reçue de {request.user.email}')
        
        # Récupérer les paramètres
        latitude = float(request.GET.get('lat', 0))
        longitude = float(request.GET.get('lng', 0))
        radius_km = float(request.GET.get('radius', 50))  # Rayon par défaut: 50km
        
        if latitude == 0 or longitude == 0:
            return Response({
                'success': False,
                'error': 'Coordonnées GPS requises (lat, lng)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f'📍 Recherche dans un rayon de {radius_km}km depuis {latitude}, {longitude}')
        
        # Récupérer tous les vendeurs actifs avec coordonnées
        vendors = Vendor.objects.filter(
            status='active',
            latitude__isnull=False,
            longitude__isnull=False,
        ).exclude(
            latitude=0,
            longitude=0,
        ).select_related('user')
        
        # Filtrer par distance (approximation simple)
        # Dans une vraie implémentation, utiliser PostGIS ou une base de données spatiale
        nearby_vendors = []
        for vendor in vendors:
            # Calcul simple de distance (formule de Haversine simplifiée)
            import math
            
            lat1, lon1 = math.radians(latitude), math.radians(longitude)
            lat2, lon2 = math.radians(float(vendor.latitude)), math.radians(float(vendor.longitude))
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Rayon de la Terre en km
            r = 6371
            distance = c * r
            
            if distance <= radius_km:
                vendor_data = {
                    'id': str(vendor.id),
                    'business_name': vendor.business_name,
                    'vendor_code': vendor.vendor_code,
                    'business_address': vendor.business_address,
                    'phone_number': vendor.phone_number,
                    'latitude': float(vendor.latitude),
                    'longitude': float(vendor.longitude),
                    'city': vendor.city,
                    'region': vendor.region,
                    'country': vendor.country,
                    'status': vendor.status,
                    'user_email': vendor.user.email,
                    'user_name': f"{vendor.user.first_name} {vendor.user.last_name}".strip(),
                    'distance_km': round(distance, 2),
                }
                nearby_vendors.append(vendor_data)
        
        # Trier par distance
        nearby_vendors.sort(key=lambda x: x['distance_km'])
        
        response_data = {
            'success': True,
            'count': len(nearby_vendors),
            'search_center': {
                'latitude': latitude,
                'longitude': longitude,
            },
            'search_radius_km': radius_km,
            'results': nearby_vendors,
        }
        
        print(f'✅ get_nearby_vendors: {len(nearby_vendors)} vendeurs trouvés')
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f'❌ get_nearby_vendors: Erreur: {str(e)}')
        return Response({
            'success': False,
            'error': f'Erreur lors de la recherche de vendeurs proches: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_vendor_details(request, vendor_id):
    """Récupérer les détails d'un vendeur spécifique"""
    try:
        print(f'🔄 get_vendor_details: Requête pour le vendeur {vendor_id}')
        
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Vendeur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        vendor_data = {
            'id': str(vendor.id),
            'business_name': vendor.business_name,
            'vendor_code': vendor.vendor_code,
            'business_address': vendor.business_address,
            'phone_number': vendor.phone_number,
            'latitude': float(vendor.latitude) if vendor.latitude else None,
            'longitude': float(vendor.longitude) if vendor.longitude else None,
            'city': vendor.city,
            'region': vendor.region,
            'country': vendor.country,
            'status': vendor.status,
            'user_email': vendor.user.email,
            'user_name': f"{vendor.user.first_name} {vendor.user.last_name}".strip(),
            'created_at': vendor.created_at.isoformat(),
            'updated_at': vendor.updated_at.isoformat(),
        }
        
        print(f'✅ get_vendor_details: Détails du vendeur {vendor.business_name} retournés')
        return Response({
            'success': True,
            'vendor': vendor_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f'❌ get_vendor_details: Erreur: {str(e)}')
        return Response({
            'success': False,
            'error': f'Erreur lors de la récupération des détails: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
