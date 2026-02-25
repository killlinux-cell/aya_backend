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
from authentication.models_grand_prix import GrandPrix, GrandPrixParticipation, GrandPrixPrize
from qr_codes.models import QRCode, UserQRCode, GameHistory, ExchangeRequest, ExchangeToken
from django.core.paginator import Paginator
import csv

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
    
    # Statistiques des grands prix
    now = timezone.now()
    current_grand_prix = GrandPrix.objects.filter(
        start_date__lte=now,
        end_date__gte=now,
        status='active'
    ).first()
    
    total_grand_prizes = GrandPrix.objects.count()
    total_participations = GrandPrixParticipation.objects.count()
    current_participations = 0
    current_grand_prix_info = None
    
    if current_grand_prix:
        current_participations = GrandPrixParticipation.objects.filter(grand_prix=current_grand_prix).count()
        current_grand_prix_info = {
            'id': str(current_grand_prix.id),
            'name': current_grand_prix.name,
            'description': current_grand_prix.description,
            'participation_cost': current_grand_prix.participation_cost,
            'start_date': current_grand_prix.start_date,
            'end_date': current_grand_prix.end_date,
            'draw_date': current_grand_prix.draw_date,
            'participants_count': current_participations,
            'prizes': GrandPrixPrize.objects.filter(grand_prix=current_grand_prix).order_by('position')
        }
    
    # Statistiques QR par catégorie
    generated_by_category = QRCode.objects.values('category').annotate(
        total_generated=Count('id'),
        active_generated=Count('id', filter=Q(is_active=True)),
        total_points=Sum('points')
    )
    scanned_by_category = UserQRCode.objects.values('qr_code__category').annotate(
        total_scans=Count('id'),
        points_distributed=Sum('points_earned')
    )

    generated_map = {item['category']: item for item in generated_by_category}
    scanned_map = {item['qr_code__category']: item for item in scanned_by_category}

    qr_category_stats = []
    for key, label in QRCode.CATEGORY_CHOICES:
        gen = generated_map.get(key, {})
        scan = scanned_map.get(key, {})
        total_generated = gen.get('total_generated', 0) or 0
        total_scans = scan.get('total_scans', 0) or 0
        scan_rate = round((total_scans / total_generated) * 100, 1) if total_generated else 0

        qr_category_stats.append({
            'key': key,
            'label': label,
            'generated': total_generated,
            'active': gen.get('active_generated', 0) or 0,
            'scans': total_scans,
            'scan_rate': scan_rate,
            'points_generated': gen.get('total_points', 0) or 0,
            'points_distributed': scan.get('points_distributed', 0) or 0,
        })

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
        'total_grand_prizes': total_grand_prizes,
        'total_participations': total_participations,
        'current_grand_prix': current_grand_prix_info,
        'qr_category_stats': qr_category_stats,
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
    users = User.objects.select_related('profile').all()
    
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(profile__phone_number__icontains=search)
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
def export_users_csv(request):
    """Exporter la liste des utilisateurs au format CSV."""
    timestamp = timezone.now().strftime('%Y%m%d_%H%M')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="utilisateurs_{timestamp}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Nom complet',
        'Email',
        'Téléphone',
        'Points disponibles',
        'Date d’inscription',
    ])

    users = User.objects.select_related('profile').order_by('last_name', 'first_name')
    for user in users:
        profile = getattr(user, 'profile', None)
        phone = getattr(profile, 'phone_number', '') if profile else ''
        writer.writerow([
            user.get_full_name(),
            user.email,
            phone,
            getattr(user, 'available_points', 0),
            user.created_at.strftime('%d/%m/%Y %H:%M') if hasattr(user, 'created_at') else '',
        ])

    return response

@login_required
@user_passes_test(is_admin)
def analytics(request):
    """Page d'analytics avec graphiques avancés + filtres/export."""
    
    # Filtres de date
    today = timezone.now().date()
    default_start = today - timedelta(days=7)
    
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    
    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else default_start
    except ValueError:
        date_from = default_start
    
    try:
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else today
    except ValueError:
        date_to = today
    
    if date_to < date_from:
        date_from, date_to = date_to, date_from
    
    days_range = (date_to - date_from).days + 1
    
    # Scans par jour
    daily_scans = []
    for i in range(days_range):
        current_date = date_from + timedelta(days=i)
        count = UserQRCode.objects.filter(
            scanned_at__date=current_date
        ).count()
        daily_scans.append({
            'date': current_date.strftime('%d/%m'),
            'count': count
        })
    
    # Points distribués par jour
    daily_points = []
    for i in range(days_range):
        current_date = date_from + timedelta(days=i)
        points = UserQRCode.objects.filter(
            scanned_at__date=current_date
        ).aggregate(total=Sum('points_earned'))['total'] or 0
        daily_points.append({
            'date': current_date.strftime('%d/%m'),
            'points': points
        })
    
    # Jeux par jour
    daily_games = []
    for i in range(days_range):
        current_date = date_from + timedelta(days=i)
        spin_wheel_count = GameHistory.objects.filter(
            game_type='spin_wheel',
            played_at__date=current_date
        ).count()
        scratch_count = GameHistory.objects.filter(
            game_type='scratch_and_win',
            played_at__date=current_date
        ).count()
        daily_games.append({
            'date': current_date.strftime('%d/%m'),
            'spin_wheel': spin_wheel_count,
            'scratch_and_win': scratch_count,
        })
    
    # Tokens d'échange par jour
    daily_tokens = []
    for i in range(days_range):
        current_date = date_from + timedelta(days=i)
        created_count = ExchangeToken.objects.filter(
            created_at__date=current_date
        ).count()
        used_count = ExchangeToken.objects.filter(
            used_at__date=current_date
        ).count()
        daily_tokens.append({
            'date': current_date.strftime('%d/%m'),
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
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'dashboard/analytics.html', context)


@login_required
@user_passes_test(is_admin)
def export_analytics_csv(request):
    """Exporter les données Analytics au format CSV (Excel compatible)."""
    today = timezone.now().date()
    default_start = today - timedelta(days=7)
    
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    
    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else default_start
    except ValueError:
        date_from = default_start
    
    try:
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else today
    except ValueError:
        date_to = today
    
    if date_to < date_from:
        date_from, date_to = date_to, date_from
    
    filename = f"analytics_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.csv"
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date',
        'Nombre de scans',
        'Points distribués',
        'Jeux Spin Wheel',
        'Jeux Scratch & Win',
        'Tokens créés',
        'Tokens utilisés',
    ])
    
    days_range = (date_to - date_from).days + 1
    for i in range(days_range):
        current_date = date_from + timedelta(days=i)
        
        scans_count = UserQRCode.objects.filter(
            scanned_at__date=current_date
        ).count()
        points_total = UserQRCode.objects.filter(
            scanned_at__date=current_date
        ).aggregate(total=Sum('points_earned'))['total'] or 0
        spin_wheel_count = GameHistory.objects.filter(
            game_type='spin_wheel',
            played_at__date=current_date
        ).count()
        scratch_count = GameHistory.objects.filter(
            game_type='scratch_and_win',
            played_at__date=current_date
        ).count()
        tokens_created = ExchangeToken.objects.filter(
            created_at__date=current_date
        ).count()
        tokens_used = ExchangeToken.objects.filter(
            used_at__date=current_date
        ).count()
        
        writer.writerow([
            current_date.strftime('%Y-%m-%d'),
            scans_count,
            points_total,
            spin_wheel_count,
            scratch_count,
            tokens_created,
            tokens_used,
        ])
    
    return response

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
    qr_url = f"https://monuniversaya.com/scan?code={qr_code.code}"
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
    qr_url = f"https://monuniversaya.com/scan?code={qr_code.code}"
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


def generate_standard_scenario(request, batch_number):
    """Génère automatiquement le scénario standard de 50 000 QR codes"""
    print(f"🎯 MODE STANDARD : Génération du scénario complet pour le lot {batch_number}")
    
    # Scénario standard selon vos spécifications
    batches_config = [
        # Points
        {'type': 'points', 'points': 10, 'quantity': 25000, 'category': '0.5L', 'desc': '10 points'},
        {'type': 'points', 'points': 50, 'quantity': 15000, 'category': '0.9L', 'desc': '50 points'},
        {'type': 'points', 'points': 100, 'quantity': 5000, 'category': '5L', 'desc': '100 points'},
        # Try Again
        {'type': 'try_again', 'points': 0, 'quantity': 4500, 'category': '0.5L', 'desc': 'Try Again'},
        # Special
        {'type': 'loyalty_bonus', 'points': 0, 'quantity': 500, 'category': '3L', 'desc': 'Loyalty Bonus'},
    ]
    
    total_generated = 0
    sequence = 1
    
    for config in batches_config:
        prize_type = config['type']
        points = config['points']
        quantity = config['quantity']
        category = config['category']
        description_type = config['desc']
        
        print(f"📦 Génération : {quantity} × {description_type} ({category})...")
        
        for i in range(quantity):
            code = f"{batch_number}{sequence:05d}"
            QRCode.objects.create(
                code=code,
                points=points,
                description=f"Lot {batch_number} - {description_type} - {category} - QR #{sequence}",
                prize_type=prize_type,
                category=category,
                is_active=True,
                created_by=request.user,
                batch_number=batch_number,
                batch_sequence=sequence,
                is_printed=True
            )
            sequence += 1
            total_generated += 1
            
            # Progrès tous les 5000 QR
            if total_generated % 5000 == 0:
                print(f"✅ {total_generated} QR codes générés...")
    
    print(f"🎉 TERMINÉ : {total_generated} QR codes générés selon le scénario standard!")
    
    # Statistiques
    stats = {
        'batch_number': batch_number,
        'total_generated': total_generated,
        'mode': 'standard',
        'breakdown': {
            '10_points': 25000,
            '50_points': 15000,
            '100_points': 5000,
            'try_again': 4500,
            'loyalty_bonus': 500
        }
    }
    
    messages.success(request, f'🎉 Scénario Standard généré ! {total_generated} QR codes créés (Lot {batch_number})')
    return JsonResponse({
        'success': True,
        'stats': stats,
        'message': f'Lot {batch_number} généré avec succès selon le scénario standard.'
    })


@login_required
@user_passes_test(is_admin)
def generate_batch_qr_codes(request):
    """Générer un lot de QR codes avec configuration personnalisée (Batch, Quantity, Category, Type)"""
    
    if request.method == 'POST':
        try:
            # Récupérer le mode de génération
            generation_mode = request.POST.get('generation_mode', 'custom')
            batch_number = request.POST.get('batch_number', '4151000')
            
            # Vérifier si le lot existe déjà
            if QRCode.objects.filter(batch_number=batch_number).exists():
                messages.error(request, f'Le lot {batch_number} existe déjà ! Choisissez un autre numéro de lot.')
                return redirect('dashboard:bulk_operations')
            
            # MODE STANDARD : Génération automatique selon scénario
            if generation_mode == 'standard':
                return generate_standard_scenario(request, batch_number)
            
            # MODE PERSONNALISÉ : Configuration manuelle
            total_qr_codes = int(request.POST.get('total_qr_codes', 50000))
            category = request.POST.get('category', '0.5L')
            prize_type = request.POST.get('prize_type', 'points')
            
            # Déterminer les points ou le type spécial
            points_value = 0
            special_type = None
            actual_prize_type = prize_type
            
            if prize_type == 'points':
                points_value = int(request.POST.get('points_value', 10))
                actual_prize_type = 'points'
            elif prize_type == 'special':
                special_type = request.POST.get('special_type', 'loyalty_bonus')
                actual_prize_type = special_type
                points_value = 0  # Les spéciaux n'ont pas de points
                
                # Si c'est une Mystery Box, récupérer les lots sélectionnés
                mystery_box_lots = {}
                if special_type == 'mystery_box':
                    mystery_box_lot_ids = [
                        'margarine_250g', 'huile_0_45L', 'bonus_50pts', 'huile_0_9L',
                        'huile_3L', 'box_aya_mix', 'carton_0_9L_12', '2x5L',
                        'carton_5L_4', 'electromenager'
                    ]
                    for lot_id in mystery_box_lot_ids:
                        quantity = request.POST.get(f'mystery_box_lot_{lot_id}')
                        if quantity and int(quantity) > 0:
                            lot_name_map = {
                                'margarine_250g': 'Margarine 250g',
                                'huile_0_45L': 'Huile 0,45L',
                                'bonus_50pts': 'Bonus 50 pts',
                                'huile_0_9L': 'Huile 0,9L',
                                'huile_3L': 'Huile 3L',
                                'box_aya_mix': 'Box Aya mix',
                                'carton_0_9L_12': 'Carton 0,9L (12)',
                                '2x5L': '2×5L',
                                'carton_5L_4': 'Carton 5L (4)',
                                'electromenager': 'Électroménager'
                            }
                            mystery_box_lots[lot_id] = {
                                'name': lot_name_map.get(lot_id, lot_id),
                                'quantity': int(quantity)
                            }
            elif prize_type == 'try_again':
                actual_prize_type = 'try_again'
                points_value = 0  # Try again n'a pas de points
            
            total_codes = total_qr_codes
            
            # Déterminer la description
            if actual_prize_type == 'points':
                type_description = f"{points_value} points"
            elif actual_prize_type == 'try_again':
                type_description = "Réessayer"
            else:
                type_description = actual_prize_type.replace('_', ' ').title()
            
            print(f"🚀 Génération du lot {batch_number}:")
            print(f"   - Nombre: {total_codes} QR codes")
            print(f"   - Catégorie: {category}")
            print(f"   - Type: {actual_prize_type}")
            print(f"   - Points: {points_value}")
            
            generated_codes = []
            sequence = 1
            
            # Si Mystery Box, préparer la distribution des lots
            mystery_box_distribution = []
            if actual_prize_type == 'mystery_box' and mystery_box_lots:
                import random
                # Créer une liste avec les lots selon leurs quantités
                for lot_id, lot_data in mystery_box_lots.items():
                    for _ in range(lot_data['quantity']):
                        mystery_box_distribution.append(lot_data['name'])
                # Mélanger pour distribution aléatoire
                random.shuffle(mystery_box_distribution)
                print(f"📦 Distribution Mystery Box : {len(mystery_box_distribution)} lots préparés")
            
            # Générer tous les QR codes avec la même configuration
            print(f"📦 Génération de {total_codes} QR codes {type_description}...")
            
            for i in range(total_codes):
                code = f"{batch_number}{sequence:05d}"
                
                # Si Mystery Box, assigner un lot aléatoire
                description = f"Lot {batch_number} - {type_description} - {category} - QR #{sequence}"
                if actual_prize_type == 'mystery_box' and mystery_box_distribution:
                    # Utiliser modulo pour distribuer de manière cyclique si pas assez de lots
                    lot_index = (i % len(mystery_box_distribution)) if mystery_box_distribution else 0
                    assigned_lot = mystery_box_distribution[lot_index] if lot_index < len(mystery_box_distribution) else "Lot surprise"
                    description = f"Lot {batch_number} - Mystery Box ({assigned_lot}) - {category} - QR #{sequence}"
                
                qr_code = QRCode.objects.create(
                    code=code,
                    points=points_value,
                    description=description,
                    prize_type=actual_prize_type,
                    category=category,
                    is_active=True,
                    created_by=request.user,
                    batch_number=batch_number,
                    batch_sequence=sequence,
                    is_printed=True
                )
                generated_codes.append({
                    'code': qr_code.code,
                    'points': qr_code.points,
                    'type': type_description,
                    'category': category
                })
                sequence += 1
                
                # Afficher le progrès tous les 1000 QR codes
                if i > 0 and i % 1000 == 0:
                    print(f"✅ {i} QR codes générés...")
            
            print(f"✅ TERMINÉ : {total_codes} QR codes générés!")
            
            # Statistiques du lot
            stats = {
                'batch_number': batch_number,
                'total_generated': total_codes,
                'category': category,
                'prize_type': actual_prize_type,
                'points_value': points_value,
                'type_description': type_description,
                'total_points_distributed': total_codes * points_value
            }
            
            messages.success(request, f'🎉 Lot {batch_number} généré avec succès ! {total_codes} QR codes créés et prêts pour l\'impression.')
            return JsonResponse({
                'success': True,
                'stats': stats,
                'message': f'Lot {batch_number} généré avec succès ! {total_codes} QR codes créés.'
            })
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération du lot: {str(e)}")
            messages.error(request, f'Erreur lors de la génération du lot: {str(e)}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
@user_passes_test(is_admin)
def batch_generation_page(request):
    """Page d'affichage pour la génération de lot de QR codes"""
    return render(request, 'dashboard/generate_batch.html')


@login_required
def loyalty_bonus_status(request):
    """Vérifier si l'utilisateur a des QR codes loyalty_bonus disponibles"""
    try:
        user = request.user
        
        # Récupérer les QR codes loyalty_bonus scannés par l'utilisateur
        loyalty_qr_codes = UserQRCode.objects.filter(
            user=user,
            qr_code__prize_type='loyalty_bonus',
            qr_code__is_active=True
        ).select_related('qr_code')
        
        # Vérifier s'il y a des QR codes non utilisés pour les jeux
        available_loyalty_codes = loyalty_qr_codes.filter(
            qr_code__is_active=True
        )
        
        has_loyalty_bonus = available_loyalty_codes.exists()
        loyalty_bonus_qr_code = None
        
        if has_loyalty_bonus:
            # Prendre le premier QR code disponible
            first_code = available_loyalty_codes.first()
            loyalty_bonus_qr_code = first_code.qr_code.code
        
        return JsonResponse({
            'has_loyalty_bonus': has_loyalty_bonus,
            'loyalty_bonus_qr_code': loyalty_bonus_qr_code,
            'available_count': available_loyalty_codes.count(),
        })
        
    except Exception as e:
        return JsonResponse({
            'has_loyalty_bonus': False,
            'loyalty_bonus_qr_code': None,
            'error': str(e)
        }, status=500)


@login_required
def mystery_box_available(request):
    """Vérifier si l'utilisateur a des QR codes mystery_box disponibles"""
    try:
        user = request.user
        
        # Récupérer les QR codes mystery_box scannés par l'utilisateur
        mystery_qr_codes = UserQRCode.objects.filter(
            user=user,
            qr_code__prize_type='mystery_box',
            qr_code__is_active=True
        ).select_related('qr_code')
        
        has_mystery_box = mystery_qr_codes.exists()
        
        return JsonResponse({
            'has_mystery_box': has_mystery_box,
            'available_count': mystery_qr_codes.count(),
        })
        
    except Exception as e:
        return JsonResponse({
            'has_mystery_box': False,
            'error': str(e)
        }, status=500)


@login_required
def open_mystery_box(request):
    """Ouvrir une Mystery Box et révéler le prix"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        qr_code = data.get('qr_code')
        
        if not qr_code:
            return JsonResponse({'error': 'QR code requis'}, status=400)
        
        user = request.user
        
        # Vérifier que l'utilisateur a ce QR code mystery_box
        user_qr_code = UserQRCode.objects.filter(
            user=user,
            qr_code__code=qr_code,
            qr_code__prize_type='mystery_box',
            qr_code__is_active=True
        ).first()
        
        if not user_qr_code:
            return JsonResponse({
                'error': 'QR code Mystery Box non trouvé ou déjà utilisé'
            }, status=404)
        
        qr_code_obj = user_qr_code.qr_code
        description = qr_code_obj.description or ''
        
        # Extraire le lot depuis la description (format: "Lot X - Mystery Box (Nom du lot) - ...")
        import re
        prize_value = 0
        prize_description = ''
        selected_prize_type = 'physical_prize'
        is_special_prize = False
        
        match = re.search(r'Mystery Box\s*\(([^)]+)\)', description)
        if match:
            # Lot configuré par l'admin (Margarine 250g, Huile 0,45L, etc.)
            assigned_lot = match.group(1).strip()
            prize_description = assigned_lot
            
            # Bonus 50 pts : créditer les points
            if 'Bonus 50 pts' in assigned_lot or 'Bonus 50 points' in assigned_lot:
                prize_value = 50
                selected_prize_type = 'points'
                prize_description = '50 points'
            # Lots physiques (Margarine, Huile, Box Aya, etc.)
            elif any(x in assigned_lot for x in ['Électroménager', 'Carton 5L', '2×5L', 'Box Aya']):
                is_special_prize = True
            else:
                selected_prize_type = 'physical_prize'
        else:
            # Fallback : ancien système aléatoire (pour QR codes générés avant la nouvelle config)
            import random
            prize_types = [
                ('points', 0.4),
                ('special_prize', 0.1),
                ('bonus_game', 0.2),
                ('loyalty_bonus', 0.2),
                ('try_again', 0.1),
            ]
            rand = random.random()
            cumulative = 0
            for prize_type, probability in prize_types:
                cumulative += probability
                if rand <= cumulative:
                    selected_prize_type = prize_type
                    break
            
            if selected_prize_type == 'points':
                prize_value = random.choice([20, 30, 50, 75, 100])
                prize_description = f'{prize_value} points'
            elif selected_prize_type == 'special_prize':
                special_prizes = [
                    ('500 points', 500),
                    ('Jeu gratuit illimité', 0),
                    ('Bonus fidélité x3', 0),
                ]
                prize_desc, prize_value = random.choice(special_prizes)
                prize_description = prize_desc
                is_special_prize = True
            elif selected_prize_type == 'bonus_game':
                prize_description = 'Jeu bonus gratuit'
                prize_value = 0
            elif selected_prize_type == 'loyalty_bonus':
                prize_description = 'QR code Bonus Fidélité'
                prize_value = 0
            elif selected_prize_type == 'try_again':
                prize_description = 'Réessayer plus tard'
                prize_value = 0
        
        # Créer l'historique de la Mystery Box
        from .models import MysteryBoxHistory
        mystery_history = MysteryBoxHistory.objects.create(
            user=user,
            qr_code=user_qr_code.qr_code,
            prize_type=selected_prize_type,
            prize_value=prize_value,
            prize_description=prize_description,
            is_special_prize=is_special_prize,
        )
        
        # Si c'est des points, les ajouter au profil utilisateur
        if selected_prize_type == 'points' and prize_value > 0:
            user.available_points += prize_value
            user.save()
        
        # Marquer le QR code comme utilisé
        user_qr_code.qr_code.is_active = False
        user_qr_code.qr_code.save()
        
        return JsonResponse({
            'success': True,
            'prize_type': selected_prize_type,
            'prize_value': prize_value,
            'prize_description': prize_description,
            'is_special_prize': is_special_prize,
            'message': f'Félicitations ! Vous avez gagné : {prize_description}',
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Erreur lors de l\'ouverture de la Mystery Box: {str(e)}'
        }, status=500)


@login_required
def mystery_box_history(request):
    """Récupérer l'historique des Mystery Box ouvertes"""
    try:
        user = request.user
        
        # Récupérer l'historique des Mystery Box
        from .models import MysteryBoxHistory
        history = MysteryBoxHistory.objects.filter(user=user).order_by('-opened_at')
        
        history_data = []
        for item in history:
            history_data.append({
                'id': str(item.id),
                'qr_code': item.qr_code.code,
                'prize_type': item.prize_type,
                'prize_value': item.prize_value,
                'prize_description': item.prize_description,
                'opened_at': item.opened_at.isoformat(),
                'is_special_prize': item.is_special_prize,
            })
        
        return JsonResponse({
            'results': history_data,
            'total': len(history_data),
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Erreur lors de la récupération de l\'historique: {str(e)}'
        }, status=500)


@login_required
def mystery_box_stats(request):
    """Récupérer les statistiques des Mystery Box"""
    try:
        user = request.user
        
        # Récupérer les statistiques
        from .models import MysteryBoxHistory
        from django.db.models import Sum, Count, Avg
        
        stats = MysteryBoxHistory.objects.filter(user=user).aggregate(
            total_opened=Count('id'),
            total_value=Sum('prize_value'),
            special_prizes=Count('id', filter=Q(is_special_prize=True)),
            average_value=Avg('prize_value'),
        )
        
        # Dernière Mystery Box ouverte
        last_opened = MysteryBoxHistory.objects.filter(user=user).order_by('-opened_at').first()
        
        return JsonResponse({
            'total_opened': stats['total_opened'] or 0,
            'total_value': stats['total_value'] or 0,
            'special_prizes': stats['special_prizes'] or 0,
            'average_value': float(stats['average_value'] or 0),
            'last_opened': last_opened.opened_at.isoformat() if last_opened else None,
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Erreur lors de la récupération des statistiques: {str(e)}'
        }, status=500)


@login_required
def available_vendors(request):
    """Récupérer la liste des vendeurs disponibles"""
    try:
        # Récupérer tous les vendeurs actifs
        from authentication.models import Vendor
        vendors = Vendor.objects.filter(status='active').order_by('business_name')
        
        vendors_data = []
        for vendor in vendors:
            vendors_data.append({
                'id': str(vendor.id),
                'business_name': vendor.business_name,
                'business_address': vendor.business_address,
                'phone_number': vendor.phone_number,
                'city': vendor.city or '',
                'region': vendor.region or '',
                'status': vendor.status,
                'latitude': vendor.latitude,
                'longitude': vendor.longitude,
            })
        
        return JsonResponse({
            'results': vendors_data,
            'total': len(vendors_data),
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Erreur lors de la récupération des vendeurs: {str(e)}'
        }, status=500)


@login_required
def search_vendors(request):
    """Rechercher des vendeurs par nom ou ville"""
    try:
        query = request.GET.get('q', '').strip()
        
        if not query:
            return JsonResponse({
                'results': [],
                'total': 0,
                'message': 'Terme de recherche requis'
            })
        
        from authentication.models import Vendor
        from django.db.models import Q
        
        # Recherche dans le nom d'entreprise, l'adresse, la ville et la région
        vendors = Vendor.objects.filter(
            Q(business_name__icontains=query) |
            Q(business_address__icontains=query) |
            Q(city__icontains=query) |
            Q(region__icontains=query),
            status='active'
        ).order_by('business_name')
        
        vendors_data = []
        for vendor in vendors:
            vendors_data.append({
                'id': str(vendor.id),
                'business_name': vendor.business_name,
                'business_address': vendor.business_address,
                'phone_number': vendor.phone_number,
                'city': vendor.city or '',
                'region': vendor.region or '',
                'status': vendor.status,
                'latitude': vendor.latitude,
                'longitude': vendor.longitude,
            })
        
        return JsonResponse({
            'results': vendors_data,
            'total': len(vendors_data),
            'query': query,
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Erreur lors de la recherche de vendeurs: {str(e)}'
        }, status=500)


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
            
            # Données de localisation
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            city = request.POST.get('city')
            region = request.POST.get('region')
            
            # Créer l'utilisateur
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            # Créer le profil vendeur (le vendor_code sera généré automatiquement)
            vendor = Vendor.objects.create(
                user=user,
                business_name=business_name,
                business_address=business_address,
                phone_number=phone_number,
                status='active',
                created_by=request.user,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                city=city,
                region=region,
            )
            
            messages.success(request, f'Vendeur {business_name} créé avec succès!')
            return redirect('dashboard:vendors')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du vendeur: {str(e)}')
    
    return render(request, 'dashboard/create_vendor.html')


@login_required
@user_passes_test(is_admin)
def create_vendor_from_existing_user(request):
    """Créer un vendeur à partir d'un utilisateur existant"""
    
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            business_name = request.POST.get('business_name')
            business_address = request.POST.get('business_address')
            phone_number = request.POST.get('phone_number')
            
            # Données de localisation
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            city = request.POST.get('city')
            region = request.POST.get('region')
            
            # Récupérer l'utilisateur existant
            user = User.objects.get(id=user_id)
            
            # Vérifier que l'utilisateur n'est pas déjà vendeur
            if Vendor.objects.filter(user=user).exists():
                messages.error(request, 'Cet utilisateur est déjà vendeur!')
                return redirect('dashboard:create_vendor_from_existing')
            
            # Créer le profil vendeur (le vendor_code sera généré automatiquement)
            vendor = Vendor.objects.create(
                user=user,
                business_name=business_name,
                business_address=business_address,
                phone_number=phone_number,
                status='active',
                created_by=request.user,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                city=city,
                region=region,
            )
            
            messages.success(request, f'Vendeur {business_name} créé à partir de {user.email}!')
            return redirect('dashboard:vendors')
            
        except User.DoesNotExist:
            messages.error(request, 'Utilisateur non trouvé!')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du vendeur: {str(e)}')
    
    # Récupérer tous les utilisateurs qui ne sont pas déjà vendeurs
    existing_vendor_user_ids = Vendor.objects.values_list('user_id', flat=True)
    available_users = User.objects.exclude(id__in=existing_vendor_user_ids).order_by('email')
    
    context = {
        'available_users': available_users,
    }
    
    return render(request, 'dashboard/create_vendor_from_existing.html', context)


@login_required
@user_passes_test(is_admin)
def search_users_for_vendor(request):
    """API pour rechercher des utilisateurs pour créer un vendeur"""
    
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    # Récupérer les utilisateurs qui ne sont pas déjà vendeurs
    existing_vendor_user_ids = Vendor.objects.values_list('user_id', flat=True)
    users = User.objects.exclude(id__in=existing_vendor_user_ids).filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    )[:10]
    
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'display_name': f"{user.first_name} {user.last_name} ({user.email})"
        })
    
    return JsonResponse({'users': users_data})


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
    
    # Nettoyer automatiquement les tokens expirés avant d'afficher
    from qr_codes.tasks import cleanup_expired_tokens
    cleanup_expired_tokens()
    
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
def cleanup_expired_tokens(request):
    """Nettoyage manuel des tokens expirés"""
    from qr_codes.tasks import cleanup_expired_tokens
    
    try:
        # Exécuter le nettoyage
        cleanup_expired_tokens()
        
        messages.success(request, 'Nettoyage des tokens expirés effectué avec succès. Les points ont été restaurés aux utilisateurs.')
    except Exception as e:
        messages.error(request, f'Erreur lors du nettoyage: {str(e)}')
    
    return redirect('dashboard:exchange_tokens_management')


@login_required
@user_passes_test(is_admin)
def token_stats_api(request):
    """API JSON pour le modal de statistiques des tokens."""
    try:
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        total_tokens = ExchangeToken.objects.count()
        active_tokens = ExchangeToken.objects.filter(
            is_used=False,
            expires_at__gt=now
        ).count()
        expired_tokens = ExchangeToken.objects.filter(
            is_used=False,
            expires_at__lte=now
        ).count()
        used_tokens = ExchangeToken.objects.filter(is_used=True).count()

        daily_data = []
        for i in range(7):
            day = (week_ago + timedelta(days=i)).date()
            created = ExchangeToken.objects.filter(created_at__date=day).count()
            used = ExchangeToken.objects.filter(is_used=True, used_at__date=day).count()
            daily_data.append({
                'date': day.strftime('%d/%m'),
                'created': created,
                'used': used,
            })

        return JsonResponse({
            'total_tokens': total_tokens,
            'active_tokens': active_tokens,
            'expired_tokens': expired_tokens,
            'used_tokens': used_tokens,
            'daily': daily_data,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== GESTION DES GRANDS PRIX =====

@login_required
@user_passes_test(is_admin)
def grand_prix_management(request):
    """Gestion des grands prix"""
    
    # Filtres
    status_filter = request.GET.get('status', 'all')
    grand_prizes = GrandPrix.objects.all()
    
    if status_filter == 'active':
        now = timezone.now()
        grand_prizes = grand_prizes.filter(
            start_date__lte=now,
            end_date__gte=now,
            status='active'
        )
    elif status_filter == 'upcoming':
        now = timezone.now()
        grand_prizes = grand_prizes.filter(
            start_date__gt=now,
            status='upcoming'
        )
    elif status_filter == 'finished':
        now = timezone.now()
        grand_prizes = grand_prizes.filter(
            Q(end_date__lt=now) | Q(status='finished')
        )
    
    # Statistiques
    total_grand_prizes = GrandPrix.objects.count()
    active_grand_prizes = GrandPrix.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now(),
        status='active'
    ).count()
    upcoming_grand_prizes = GrandPrix.objects.filter(
        start_date__gt=timezone.now(),
        status='upcoming'
    ).count()
    finished_grand_prizes = GrandPrix.objects.filter(
        Q(end_date__lt=timezone.now()) | Q(status='finished')
    ).count()
    
    # Pagination
    paginator = Paginator(grand_prizes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'total_grand_prizes': total_grand_prizes,
        'active_grand_prizes': active_grand_prizes,
        'upcoming_grand_prizes': upcoming_grand_prizes,
        'finished_grand_prizes': finished_grand_prizes,
    }
    
    return render(request, 'dashboard/grand_prix.html', context)

@login_required
@user_passes_test(is_admin)
def grand_prix_detail(request, grand_prix_id):
    """Détail d'un grand prix"""
    try:
        grand_prix = GrandPrix.objects.get(id=grand_prix_id)
        
        # Récupérer les récompenses
        prizes = GrandPrixPrize.objects.filter(grand_prix=grand_prix).order_by('position')
        
        # Récupérer les participations
        participations = GrandPrixParticipation.objects.filter(
            grand_prix=grand_prix
        ).select_related('user').order_by('-participated_at')
        
        # Statistiques
        total_participants = participations.count()
        winners_count = participations.filter(is_winner=True).count()
        
        context = {
            'grand_prix': grand_prix,
            'prizes': prizes,
            'participations': participations,
            'total_participants': total_participants,
            'winners_count': winners_count,
        }
        
        return render(request, 'dashboard/grand_prix_detail.html', context)
        
    except GrandPrix.DoesNotExist:
        messages.error(request, 'Grand prix non trouvé')
        return redirect('dashboard:grand_prix_management')

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


@login_required
@user_passes_test(is_admin)
def vendors_map(request):
    """Carte des vendeurs en Côte d'Ivoire"""
    
    # Récupérer tous les vendeurs avec leurs coordonnées
    vendors = Vendor.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        status='active'
    ).select_related('user')
    
    # Statistiques par région
    region_stats = vendors.values('region').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Statistiques par ville
    city_stats = vendors.values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Préparer les données pour la carte
    vendors_data = []
    for vendor in vendors:
        vendors_data.append({
            'id': str(vendor.id),
            'name': vendor.business_name,
            'address': vendor.business_address,
            'phone': vendor.phone_number,
            'city': vendor.city,
            'region': vendor.region,
            'latitude': float(vendor.latitude),
            'longitude': float(vendor.longitude),
            'status': vendor.status,
            'created_at': vendor.created_at.strftime('%d/%m/%Y'),
        })
    
    context = {
        'vendors': vendors,
        'vendors_data': json.dumps(vendors_data),
        'region_stats': region_stats,
        'city_stats': city_stats,
        'total_vendors': vendors.count(),
    }
    
    return render(request, 'dashboard/vendors_map.html', context)


@login_required
@user_passes_test(is_admin)
def update_vendor_location(request, vendor_id):
    """Mettre à jour la localisation d'un vendeur"""
    
    try:
        vendor = Vendor.objects.get(id=vendor_id)
        
        if request.method == 'POST':
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            city = request.POST.get('city')
            region = request.POST.get('region')
            
            if latitude and longitude:
                vendor.latitude = float(latitude)
                vendor.longitude = float(longitude)
            
            if city:
                vendor.city = city
            if region:
                vendor.region = region
                
            vendor.save()
            
            messages.success(request, f'Localisation de {vendor.business_name} mise à jour!')
            return redirect('dashboard:vendors_map')
            
    except Vendor.DoesNotExist:
        messages.error(request, 'Vendeur non trouvé')
    except Exception as e:
        messages.error(request, f'Erreur: {str(e)}')
    
    return redirect('dashboard:vendors_map')