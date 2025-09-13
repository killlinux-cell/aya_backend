from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
import qrcode
import io
import base64
from django.core.files.base import ContentFile

from authentication.models import User, Vendor
from qr_codes.models import QRCode, UserQRCode, GameHistory, ExchangeRequest, ExchangeToken
from django.core.paginator import Paginator

def is_admin(user):
    """Vérifier si l'utilisateur est admin"""
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def dashboard_home(request):
    """Page d'accueil du dashboard"""
    
    # Statistiques générales
    total_users = User.objects.count()
    total_qr_codes = QRCode.objects.count()
    total_scans = UserQRCode.objects.count()
    total_points_distributed = UserQRCode.objects.aggregate(
        total=Sum('points_earned')
    )['total'] or 0
    
    # Nouvelles statistiques
    total_vendors = Vendor.objects.count()
    active_vendors = Vendor.objects.filter(status='active').count()
    total_games_played = GameHistory.objects.count()
    total_exchange_tokens = ExchangeToken.objects.count()
    active_exchange_tokens = ExchangeToken.objects.filter(is_used=False, expires_at__gt=timezone.now()).count()
    
    # Statistiques des 7 derniers jours
    week_ago = timezone.now() - timedelta(days=7)
    recent_scans = UserQRCode.objects.filter(scanned_at__gte=week_ago).count()
    recent_users = User.objects.filter(created_at__gte=week_ago).count()
    recent_games = GameHistory.objects.filter(played_at__gte=week_ago).count()
    recent_exchanges = ExchangeRequest.objects.filter(created_at__gte=week_ago).count()
    
    # QR codes les plus populaires
    popular_qr_codes = QRCode.objects.annotate(
        scan_count=Count('scanned_by_users')
    ).order_by('-scan_count')[:5]
    
    # Utilisateurs les plus actifs
    active_users = User.objects.annotate(
        scan_count=Count('scanned_qr_codes')
    ).order_by('-scan_count')[:5]
    
    # Top utilisateurs par points
    top_users_by_points = User.objects.order_by('-available_points')[:5]
    
    # Demandes d'échange en attente
    pending_exchanges = ExchangeRequest.objects.filter(status='pending').count()
    
    context = {
        'total_users': total_users,
        'total_qr_codes': total_qr_codes,
        'total_scans': total_scans,
        'total_points_distributed': total_points_distributed,
        'total_vendors': total_vendors,
        'active_vendors': active_vendors,
        'total_games_played': total_games_played,
        'total_exchange_tokens': total_exchange_tokens,
        'active_exchange_tokens': active_exchange_tokens,
        'recent_scans': recent_scans,
        'recent_users': recent_users,
        'recent_games': recent_games,
        'recent_exchanges': recent_exchanges,
        'popular_qr_codes': popular_qr_codes,
        'active_users': active_users,
        'top_users_by_points': top_users_by_points,
        'pending_exchanges': pending_exchanges,
    }
    
    return render(request, 'dashboard/home.html', context)

@login_required
@user_passes_test(is_admin)
def qr_codes_management(request):
    """Gestion des QR codes"""
    
    # Filtres
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    qr_codes = QRCode.objects.all()
    
    if search:
        qr_codes = qr_codes.filter(
            Q(code__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if status_filter == 'active':
        qr_codes = qr_codes.filter(is_active=True)
    elif status_filter == 'inactive':
        qr_codes = qr_codes.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(qr_codes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/qr_codes.html', context)

@login_required
@user_passes_test(is_admin)
def create_qr_code(request):
    """Créer un nouveau QR code"""
    
    if request.method == 'POST':
        code = request.POST.get('code')
        points = request.POST.get('points')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        
        if not code or not points:
            messages.error(request, 'Le code et les points sont obligatoires')
            return redirect('dashboard:qr_codes')
        
        try:
            points = int(points)
            prize_type = request.POST.get('prize_type', 'points')
            qr_code = QRCode.objects.create(
                code=code,
                points=points,
                description=description,
                prize_type=prize_type,
                is_active=is_active,
                created_by=request.user
            )
            messages.success(request, f'QR Code "{code}" créé avec succès !')
            return redirect('dashboard:qr_codes')
        except ValueError:
            messages.error(request, 'Les points doivent être un nombre valide')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {str(e)}')
    
    return redirect('dashboard:qr_codes')

@login_required
@user_passes_test(is_admin)
def edit_qr_code(request, qr_code_id):
    """Modifier un QR code"""
    
    try:
        qr_code = QRCode.objects.get(id=qr_code_id)
    except QRCode.DoesNotExist:
        messages.error(request, 'QR Code introuvable')
        return redirect('dashboard:qr_codes')
    
    if request.method == 'POST':
        qr_code.points = int(request.POST.get('points', qr_code.points))
        qr_code.description = request.POST.get('description', qr_code.description)
        qr_code.is_active = request.POST.get('is_active') == 'on'
        qr_code.save()
        
        messages.success(request, f'QR Code "{qr_code.code}" modifié avec succès !')
        return redirect('dashboard:qr_codes')
    
    return JsonResponse({
        'id': str(qr_code.id),
        'code': qr_code.code,
        'points': qr_code.points,
        'description': qr_code.description,
        'is_active': qr_code.is_active,
    })

@login_required
@user_passes_test(is_admin)
def delete_qr_code(request, qr_code_id):
    """Supprimer un QR code"""
    
    try:
        qr_code = QRCode.objects.get(id=qr_code_id)
        code = qr_code.code
        qr_code.delete()
        messages.success(request, f'QR Code "{code}" supprimé avec succès !')
    except QRCode.DoesNotExist:
        messages.error(request, 'QR Code introuvable')
    
    return redirect('dashboard:qr_codes')

@login_required
@user_passes_test(is_admin)
def users_management(request):
    """Gestion des utilisateurs"""
    
    search = request.GET.get('search', '')
    users = User.objects.all()
    
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
    }
    
    return render(request, 'dashboard/users.html', context)

@login_required
@user_passes_test(is_admin)
def analytics(request):
    """Page d'analytics avec graphiques avancés"""
    
    # Données pour les graphiques
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Scans par jour (7 derniers jours)
    daily_scans = []
    for i in range(7):
        date = week_ago + timedelta(days=i)
        count = UserQRCode.objects.filter(
            scanned_at__date=date
        ).count()
        daily_scans.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    
    # Points distribués par jour
    daily_points = []
    for i in range(7):
        date = week_ago + timedelta(days=i)
        points = UserQRCode.objects.filter(
            scanned_at__date=date
        ).aggregate(total=Sum('points_earned'))['total'] or 0
        daily_points.append({
            'date': date.strftime('%d/%m'),
            'points': points
        })
    
    # Jeux par jour (7 derniers jours)
    daily_games = []
    for i in range(7):
        date = week_ago + timedelta(days=i)
        spin_wheel_count = GameHistory.objects.filter(
            game_type='spin_wheel',
            played_at__date=date
        ).count()
        scratch_count = GameHistory.objects.filter(
            game_type='scratch_and_win',
            played_at__date=date
        ).count()
        daily_games.append({
            'date': date.strftime('%d/%m'),
            'spin_wheel': spin_wheel_count,
            'scratch_and_win': scratch_count,
        })
    
    # Tokens d'échange par jour
    daily_tokens = []
    for i in range(7):
        date = week_ago + timedelta(days=i)
        created_count = ExchangeToken.objects.filter(
            created_at__date=date
        ).count()
        used_count = ExchangeToken.objects.filter(
            used_at__date=date
        ).count()
        daily_tokens.append({
            'date': date.strftime('%d/%m'),
            'created': created_count,
            'used': used_count,
        })
    
    # Top QR codes
    top_qr_codes = QRCode.objects.annotate(
        scan_count=Count('scanned_by_users')
    ).order_by('-scan_count')[:10]
    
    # Top utilisateurs
    top_users = User.objects.annotate(
        scan_count=Count('scanned_qr_codes'),
        total_points=Sum('scanned_qr_codes__points_earned')
    ).order_by('-scan_count')[:10]
    
    # Top vendeurs (par nombre de tokens validés)
    top_vendors = Vendor.objects.annotate(
        tokens_validated=Count('user__exchange_tokens', filter=Q(user__exchange_tokens__is_used=True))
    ).order_by('-tokens_validated')[:5]
    
    # Statistiques générales
    total_vendors = Vendor.objects.count()
    active_vendors = Vendor.objects.filter(status='active').count()
    total_games = GameHistory.objects.count()
    total_tokens = ExchangeToken.objects.count()
    used_tokens = ExchangeToken.objects.filter(is_used=True).count()
    expired_tokens = ExchangeToken.objects.filter(
        is_used=False, 
        expires_at__lte=timezone.now()
    ).count()
    
    # Taux de conversion
    conversion_rate = 0
    if total_tokens > 0:
        conversion_rate = (used_tokens / total_tokens) * 100
    
    context = {
        'daily_scans': json.dumps(daily_scans),
        'daily_points': json.dumps(daily_points),
        'daily_games': json.dumps(daily_games),
        'daily_tokens': json.dumps(daily_tokens),
        'top_qr_codes': top_qr_codes,
        'top_users': top_users,
        'top_vendors': top_vendors,
        'total_vendors': total_vendors,
        'active_vendors': active_vendors,
        'total_games': total_games,
        'total_tokens': total_tokens,
        'used_tokens': used_tokens,
        'expired_tokens': expired_tokens,
        'conversion_rate': round(conversion_rate, 1),
    }
    
    return render(request, 'dashboard/analytics.html', context)

@login_required
@user_passes_test(is_admin)
def exchange_requests(request):
    """Gestion des demandes d'échange"""
    
    status_filter = request.GET.get('status', 'all')
    exchanges = ExchangeRequest.objects.all()
    
    if status_filter != 'all':
        exchanges = exchanges.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(exchanges, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/exchanges.html', context)

@login_required
@user_passes_test(is_admin)
def update_exchange_status(request, exchange_id):
    """Mettre à jour le statut d'une demande d'échange"""
    
    try:
        exchange = ExchangeRequest.objects.get(id=exchange_id)
        new_status = request.POST.get('status')
        
        if new_status in ['approved', 'rejected', 'completed']:
            exchange.status = new_status
            if new_status == 'approved':
                exchange.approved_at = timezone.now()
                exchange.approved_by = request.user
            elif new_status == 'completed':
                exchange.completed_at = timezone.now()
            exchange.save()
            
            messages.success(request, f'Statut mis à jour: {new_status}')
        else:
            messages.error(request, 'Statut invalide')
            
    except ExchangeRequest.DoesNotExist:
        messages.error(request, 'Demande d\'échange introuvable')
    
    return redirect('dashboard:exchanges')

@login_required
@user_passes_test(is_admin)
def generate_qr_code_image(request, qr_code_id):
    """Générer l'image QR code pour un QR code spécifique"""
    
    qr_code = get_object_or_404(QRCode, id=qr_code_id)
    
    # Créer le QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # URL à encoder dans le QR code
    qr_url = f"https://aya-plus.orapide.shop/scan?code={qr_code.code}"
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    # Créer l'image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir en base64 pour l'affichage
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return JsonResponse({
        'success': True,
        'qr_code_id': str(qr_code.id),
        'code': qr_code.code,
        'points': qr_code.points,
        'description': qr_code.description,
        'qr_url': qr_url,
        'image': f"data:image/png;base64,{img_str}"
    })

@login_required
@user_passes_test(is_admin)
def download_qr_code(request, qr_code_id):
    """Télécharger l'image QR code"""
    
    qr_code = get_object_or_404(QRCode, id=qr_code_id)
    
    # Créer le QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=15,
        border=4,
    )
    
    # URL à encoder dans le QR code
    qr_url = f"https://aya-plus.orapide.shop/scan?code={qr_code.code}"
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    # Créer l'image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Préparer la réponse
    response = HttpResponse(content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_code_{qr_code.code}.png"'
    
    # Sauvegarder l'image
    img.save(response, 'PNG')
    
    return response

@login_required
@user_passes_test(is_admin)
def bulk_generate_qr_codes(request):
    """Générer plusieurs QR codes en lot"""
    
    if request.method == 'POST':
        count = int(request.POST.get('count', 10))
        points = int(request.POST.get('points', 10))
        description = request.POST.get('description', 'QR Code généré automatiquement')
        
        generated_codes = []
        
        for i in range(count):
            # Générer un code unique
            import uuid
            code = str(uuid.uuid4())[:8].upper()
            
            # Vérifier que le code n'existe pas déjà
            while QRCode.objects.filter(code=code).exists():
                code = str(uuid.uuid4())[:8].upper()
            
            # Créer le QR code
            qr_code = QRCode.objects.create(
                code=code,
                points=points,
                description=f"{description} #{i+1}",
                is_active=True,
                created_by=request.user
            )
            
            generated_codes.append({
                'id': str(qr_code.id),
                'code': qr_code.code,
                'points': qr_code.points,
                'description': qr_code.description
            })
        
        messages.success(request, f'{count} QR codes générés avec succès !')
        return JsonResponse({
            'success': True,
            'count': count,
            'codes': generated_codes
        })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


# ===== GESTION DES VENDEURS =====

@login_required
@user_passes_test(is_admin)
def vendors_management(request):
    """Gestion des vendeurs"""
    
    # Filtres
    status_filter = request.GET.get('status', 'all')
    vendors = Vendor.objects.select_related('user').all()
    
    if status_filter == 'active':
        vendors = vendors.filter(status='active')
    elif status_filter == 'inactive':
        vendors = vendors.filter(status='inactive')
    
    # Statistiques
    total_vendors = Vendor.objects.count()
    active_vendors = Vendor.objects.filter(status='active').count()
    inactive_vendors = Vendor.objects.filter(status='inactive').count()
    
    # Pagination
    paginator = Paginator(vendors, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'total_vendors': total_vendors,
        'active_vendors': active_vendors,
        'inactive_vendors': inactive_vendors,
    }
    
    return render(request, 'dashboard/vendors.html', context)


@login_required
@user_passes_test(is_admin)
def create_vendor(request):
    """Créer un nouveau vendeur"""
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            password = request.POST.get('password')
            business_name = request.POST.get('business_name')
            business_address = request.POST.get('business_address')
            phone_number = request.POST.get('phone_number')
            
            # Créer l'utilisateur
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            # Créer le profil vendeur
            vendor = Vendor.objects.create(
                user=user,
                business_name=business_name,
                business_address=business_address,
                phone_number=phone_number,
                status='active',
                created_by=request.user
            )
            
            messages.success(request, f'Vendeur {business_name} créé avec succès!')
            return redirect('dashboard:vendors')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du vendeur: {str(e)}')
    
    return render(request, 'dashboard/create_vendor.html')


@login_required
@user_passes_test(is_admin)
def update_vendor_status(request, vendor_id):
    """Mettre à jour le statut d'un vendeur"""
    
    try:
        vendor = Vendor.objects.get(id=vendor_id)
        new_status = request.POST.get('status')
        
        if new_status in ['active', 'inactive']:
            vendor.status = new_status
            vendor.updated_at = timezone.now()
            vendor.save()
            
            messages.success(request, f'Statut du vendeur {vendor.business_name} mis à jour!')
        else:
            messages.error(request, 'Statut invalide')
            
    except Vendor.DoesNotExist:
        messages.error(request, 'Vendeur non trouvé')
    except Exception as e:
        messages.error(request, f'Erreur: {str(e)}')
    
    return redirect('dashboard:vendors')


# ===== GESTION DES JEUX =====

@login_required
@user_passes_test(is_admin)
def games_management(request):
    """Gestion des jeux et historique"""
    
    # Filtres
    game_type_filter = request.GET.get('game_type', 'all')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    games = GameHistory.objects.select_related('user').all()
    
    if game_type_filter != 'all':
        games = games.filter(game_type=game_type_filter)
    
    if date_from:
        games = games.filter(played_at__date__gte=date_from)
    if date_to:
        games = games.filter(played_at__date__lte=date_to)
    
    # Statistiques
    total_games = GameHistory.objects.count()
    spin_wheel_games = GameHistory.objects.filter(game_type='spin_wheel').count()
    scratch_games = GameHistory.objects.filter(game_type='scratch_and_win').count()
    total_points_distributed = GameHistory.objects.aggregate(
        total=Sum('points_won')
    )['total'] or 0
    
    # Pagination
    paginator = Paginator(games, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'game_type_filter': game_type_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_games': total_games,
        'spin_wheel_games': spin_wheel_games,
        'scratch_games': scratch_games,
        'total_points_distributed': total_points_distributed,
    }
    
    return render(request, 'dashboard/games.html', context)


# ===== GESTION DES TOKENS D'ÉCHANGE =====

@login_required
@user_passes_test(is_admin)
def exchange_tokens_management(request):
    """Gestion des tokens d'échange temporaires"""
    
    # Filtres
    status_filter = request.GET.get('status', 'all')
    tokens = ExchangeToken.objects.select_related('user').all()
    
    if status_filter == 'active':
        tokens = tokens.filter(is_used=False, expires_at__gt=timezone.now())
    elif status_filter == 'used':
        tokens = tokens.filter(is_used=True)
    elif status_filter == 'expired':
        tokens = tokens.filter(is_used=False, expires_at__lte=timezone.now())
    
    # Statistiques
    total_tokens = ExchangeToken.objects.count()
    active_tokens = ExchangeToken.objects.filter(
        is_used=False, 
        expires_at__gt=timezone.now()
    ).count()
    used_tokens = ExchangeToken.objects.filter(is_used=True).count()
    expired_tokens = ExchangeToken.objects.filter(
        is_used=False, 
        expires_at__lte=timezone.now()
    ).count()
    
    # Pagination
    paginator = Paginator(tokens, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'total_tokens': total_tokens,
        'active_tokens': active_tokens,
        'used_tokens': used_tokens,
        'expired_tokens': expired_tokens,
    }
    
    return render(request, 'dashboard/exchange_tokens.html', context)

@login_required
@user_passes_test(is_admin)
def qr_codes_analytics(request):
    """Analytics détaillées des QR codes"""
    
    # Statistiques par type de prix
    prize_type_stats = QRCode.objects.values('prize_type').annotate(
        count=Count('id'),
        total_scans=Count('scanned_by_users'),
        avg_points=Sum('points') / Count('id')
    ).order_by('-count')
    
    # QR codes par mois de création
    monthly_stats = []
    for i in range(12):
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        monthly_count = QRCode.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        monthly_stats.append({
            'month': month_start.strftime('%Y-%m'),
            'count': monthly_count
        })
    
    # Top 10 QR codes les plus scannés
    top_scanned = QRCode.objects.annotate(
        scan_count=Count('scanned_by_users')
    ).order_by('-scan_count')[:10]
    
    # QR codes expirés
    expired_qr_codes = QRCode.objects.filter(
        expires_at__lt=timezone.now()
    ).count()
    
    # QR codes inactifs
    inactive_qr_codes = QRCode.objects.filter(is_active=False).count()
    
    context = {
        'prize_type_stats': prize_type_stats,
        'monthly_stats': monthly_stats,
        'top_scanned': top_scanned,
        'expired_qr_codes': expired_qr_codes,
        'inactive_qr_codes': inactive_qr_codes,
    }
    
    return render(request, 'dashboard/qr_codes_analytics.html', context)

@login_required
@user_passes_test(is_admin)
def system_health(request):
    """Vue de santé du système"""
    
    # Vérifications système
    health_checks = {
        'database': True,  # À implémenter
        'redis': False,    # À implémenter si utilisé
        'storage': True,   # À implémenter
        'api': True,       # À implémenter
    }
    
    # Statistiques de performance
    performance_stats = {
        'avg_response_time': 0.5,  # À implémenter
        'error_rate': 0.02,        # À implémenter
        'uptime': '99.9%',         # À implémenter
    }
    
    # Logs récents (à implémenter avec un système de logging)
    recent_errors = []
    
    context = {
        'health_checks': health_checks,
        'performance_stats': performance_stats,
        'recent_errors': recent_errors,
    }
    
    return render(request, 'dashboard/system_health.html', context)

@login_required
@user_passes_test(is_admin)
def bulk_operations(request):
    """Vue pour les opérations en lot"""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'activate_all_qr':
            QRCode.objects.filter(is_active=False).update(is_active=True)
            messages.success(request, 'Tous les QR codes ont été activés')
            
        elif action == 'deactivate_expired_qr':
            expired_count = QRCode.objects.filter(
                expires_at__lt=timezone.now(),
                is_active=True
            ).update(is_active=False)
            messages.success(request, f'{expired_count} QR codes expirés ont été désactivés')
            
        elif action == 'cleanup_old_tokens':
            old_tokens = ExchangeToken.objects.filter(
                expires_at__lt=timezone.now() - timedelta(days=30)
            ).delete()
            messages.success(request, f'{old_tokens[0]} anciens tokens ont été supprimés')
            
        return redirect('dashboard:bulk_operations')
    
    # Statistiques pour les opérations en lot
    inactive_qr_count = QRCode.objects.filter(is_active=False).count()
    expired_qr_count = QRCode.objects.filter(expires_at__lt=timezone.now()).count()
    old_tokens_count = ExchangeToken.objects.filter(
        expires_at__lt=timezone.now() - timedelta(days=30)
    ).count()
    
    context = {
        'inactive_qr_count': inactive_qr_count,
        'expired_qr_count': expired_qr_count,
        'old_tokens_count': old_tokens_count,
    }
    
    return render(request, 'dashboard/bulk_operations.html', context)