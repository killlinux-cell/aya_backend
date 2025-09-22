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


@login_required
@user_passes_test(is_admin)
def generate_batch_qr_codes(request):
    """Générer un lot de QR codes selon le scénario de bouteilles - VERSION SIMPLIFIÉE"""
    
    if request.method == 'POST':
        try:
            batch_number = request.POST.get('batch_number', '4151000')
            
            # Vérifier si le lot existe déjà
            if QRCode.objects.filter(batch_number=batch_number).exists():
                messages.error(request, f'Le lot {batch_number} existe déjà ! Choisissez un autre numéro de lot.')
                return JsonResponse({
                    'success': False,
                    'error': f'Le lot {batch_number} existe déjà !'
                })
            
            # SCÉNARIO FIXE - 50 000 QR codes exactement
            scenario = {
                '10_points': 25000,    # 50% - QR codes gagnants 10 points
                '50_points': 15000,    # 30% - QR codes gagnants 50 points  
                '100_points': 5000,    # 10% - QR codes gagnants 100 points
                'try_again': 4000,     # 8% - QR codes "Réessayer"
                'loyalty_bonus': 500,  # 1% - QR codes "Bonus Fidélité"
                'mystery_box': 500,    # 1% - QR codes "Mystery Box"
            }
            
            total_codes = sum(scenario.values())  # 50 000 exactement
            
            print(f"🚀 Génération du lot {batch_number} avec {total_codes} QR codes...")
            
            generated_codes = []
            sequence = 1
            
            # 1. Générer les QR codes gagnants (10 points) - 25 000
            print(f"📦 Génération des QR codes 10 points...")
            for i in range(scenario['10_points']):
                code = f"{batch_number}{sequence:05d}"
                qr_code = QRCode.objects.create(
                    code=code,
                    points=10,
                    description=f"Lot {batch_number} - 10 points - QR #{sequence}",
                    prize_type='points',
                    is_active=True,
                    created_by=request.user,
                    batch_number=batch_number,
                    batch_sequence=sequence,
                    is_printed=True
                )
                generated_codes.append({
                    'code': qr_code.code,
                    'points': qr_code.points,
                    'type': '10 points'
                })
                sequence += 1
                
                # Afficher le progrès tous les 5000 QR codes
                if sequence % 5000 == 1:
                    print(f"✅ {sequence-1} QR codes 10 points générés...")
            
            # 2. Générer les QR codes gagnants (50 points) - 15 000
            print(f"📦 Génération des QR codes 50 points...")
            for i in range(scenario['50_points']):
                code = f"{batch_number}{sequence:05d}"
                qr_code = QRCode.objects.create(
                    code=code,
                    points=50,
                    description=f"Lot {batch_number} - 50 points - QR #{sequence}",
                    prize_type='points',
                    is_active=True,
                    created_by=request.user,
                    batch_number=batch_number,
                    batch_sequence=sequence,
                    is_printed=True
                )
                generated_codes.append({
                    'code': qr_code.code,
                    'points': qr_code.points,
                    'type': '50 points'
                })
                sequence += 1
                
                if sequence % 5000 == 1:
                    print(f"✅ {sequence-1} QR codes 50 points générés...")
            
            # 3. Générer les QR codes gagnants (100 points) - 5 000
            print(f"📦 Génération des QR codes 100 points...")
            for i in range(scenario['100_points']):
                code = f"{batch_number}{sequence:05d}"
                qr_code = QRCode.objects.create(
                    code=code,
                    points=100,
                    description=f"Lot {batch_number} - 100 points - QR #{sequence}",
                    prize_type='points',
                    is_active=True,
                    created_by=request.user,
                    batch_number=batch_number,
                    batch_sequence=sequence,
                    is_printed=True
                )
                generated_codes.append({
                    'code': qr_code.code,
                    'points': qr_code.points,
                    'type': '100 points'
                })
                sequence += 1
                
                if sequence % 1000 == 1:
                    print(f"✅ {sequence-1} QR codes 100 points générés...")
            
            # 4. Générer les QR codes "Réessayer" - 4 500
            print(f"📦 Génération des QR codes 'Réessayer'...")
            for i in range(scenario['try_again']):
                code = f"{batch_number}{sequence:05d}"
                qr_code = QRCode.objects.create(
                    code=code,
                    points=0,
                    description=f"Lot {batch_number} - Réessayer - QR #{sequence}",
                    prize_type='try_again',
                    is_active=True,
                    created_by=request.user,
                    batch_number=batch_number,
                    batch_sequence=sequence,
                    is_printed=True
                )
                generated_codes.append({
                    'code': qr_code.code,
                    'points': qr_code.points,
                    'type': 'Réessayer'
                })
                sequence += 1
                
                if sequence % 1000 == 1:
                    print(f"✅ {sequence-1} QR codes 'Réessayer' générés...")
            
            # 5. Générer les QR codes "Bonus Fidélité" - 500
            print(f"📦 Génération des QR codes 'Bonus Fidélité'...")
            for i in range(scenario['loyalty_bonus']):
                code = f"{batch_number}{sequence:05d}"
                qr_code = QRCode.objects.create(
                    code=code,
                    points=0,
                    description=f"Lot {batch_number} - Bonus Fidélité - QR #{sequence}",
                    prize_type='loyalty_bonus',
                    is_active=True,
                    created_by=request.user,
                    batch_number=batch_number,
                    batch_sequence=sequence,
                    is_printed=True
                )
                generated_codes.append({
                    'code': qr_code.code,
                    'points': qr_code.points,
                    'type': 'Bonus Fidélité'
                })
                sequence += 1

            # Generate 'mystery_box' QR codes
            for i in range(scenario['mystery_box']):
                code = f"{batch_number}{sequence:05d}"
                qr_code = QRCode.objects.create(
                    code=code,
                    points=0,
                    description=f"Lot {batch_number} - Mystery Box - QR #{sequence}",
                    prize_type='mystery_box',
                    is_active=True,
                    created_by=request.user,
                    batch_number=batch_number,
                    batch_sequence=sequence,
                    is_printed=True
                )
                generated_codes.append({
                    'code': qr_code.code,
                    'points': qr_code.points,
                    'type': 'Mystery Box'
                })
                sequence += 1
            
            print(f"🎉 Lot {batch_number} généré avec succès ! {total_codes} QR codes créés.")
            
            # Statistiques du lot
            stats = {
                'batch_number': batch_number,
                'total_generated': len(generated_codes),
                'winning_10': scenario['10_points'],
                'winning_50': scenario['50_points'],
                'winning_100': scenario['100_points'],
                'try_again': scenario['try_again'],
                'loyalty_bonus': scenario['loyalty_bonus'],
                'mystery_box': scenario['mystery_box'],
                'total_points_distributed': (scenario['10_points'] * 10) + (scenario['50_points'] * 50) + (scenario['100_points'] * 100)
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
        
        # Générer un prix aléatoire pour la Mystery Box
        import random
        
        # Probabilités des prix (ajustables selon vos besoins)
        prize_types = [
            ('points', 0.4),      # 40% - Points
            ('special_prize', 0.1), # 10% - Prix spécial
            ('bonus_game', 0.2),   # 20% - Jeu bonus
            ('loyalty_bonus', 0.2), # 20% - Bonus fidélité
            ('try_again', 0.1),    # 10% - Réessayer
        ]
        
        # Sélectionner le type de prix
        rand = random.random()
        cumulative = 0
        selected_prize_type = 'points'
        
        for prize_type, probability in prize_types:
            cumulative += probability
            if rand <= cumulative:
                selected_prize_type = prize_type
                break
        
        # Déterminer la valeur du prix
        prize_value = 0
        prize_description = ''
        is_special_prize = False
        
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