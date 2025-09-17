from django.contrib import admin
from .models import QRCode, UserQRCode, GameHistory, DailyGameLimit, ExchangeRequest, ExchangeToken

@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'points', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'points')
    search_fields = ('code', 'description')
    readonly_fields = ('code', 'created_at')
    list_per_page = 25

@admin.register(UserQRCode)
class UserQRCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'qr_code', 'points_earned', 'scanned_at')
    list_filter = ('scanned_at', 'points_earned')
    search_fields = ('user__email', 'qr_code__code')
    readonly_fields = ('scanned_at',)
    list_per_page = 25
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'qr_code')

@admin.register(GameHistory)
class GameHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'game_type', 'points_spent', 'points_won', 'is_winning', 'played_at')
    list_filter = ('game_type', 'is_winning', 'played_at')
    search_fields = ('user__email', 'game_type')
    readonly_fields = ('played_at',)
    list_per_page = 25
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(DailyGameLimit)
class DailyGameLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'game_type', 'games_played', 'date')
    list_filter = ('game_type', 'date')
    search_fields = ('user__email', 'game_type')
    list_per_page = 25
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(ExchangeRequest)
class ExchangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 
        'points', 
        'exchange_code', 
        'status', 
        'vendor_info',
        'created_at', 
        'completed_at'
    )
    list_filter = ('status', 'created_at', 'completed_at', 'approved_by')
    search_fields = (
        'user__email', 
        'exchange_code', 
        'approved_by__email',
        'approved_by__vendor_profile__business_name'
    )
    readonly_fields = (
        'exchange_code', 
        'created_at', 
        'completed_at',
        'approved_at'
    )
    list_per_page = 25
    
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'user', 
                'points', 
                'exchange_code', 
                'status'
            )
        }),
        ('Validation vendeur', {
            'fields': (
                'approved_by', 
                'approved_at', 
                'completed_at'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email Client'
    user_email.admin_order_field = 'user__email'
    
    def vendor_info(self, obj):
        if obj.approved_by and hasattr(obj.approved_by, 'vendor_profile'):
            return f"{obj.approved_by.vendor_profile.business_name} ({obj.approved_by.vendor_profile.vendor_code})"
        return "N/A"
    vendor_info.short_description = 'Vendeur'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 
            'approved_by__vendor_profile'
        )
    
    actions = ['approve_exchanges', 'reject_exchanges']
    
    def approve_exchanges(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='completed',
            approved_by=request.user,
            approved_at=timezone.now(),
            completed_at=timezone.now()
        )
        self.message_user(request, f'{updated} échange(s) approuvé(s) avec succès.')
    approve_exchanges.short_description = "Approuver les échanges sélectionnés"
    
    def reject_exchanges(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f'{updated} échange(s) rejeté(s) avec succès.')
    reject_exchanges.short_description = "Rejeter les échanges sélectionnés"

@admin.register(ExchangeToken)
class ExchangeTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'token', 'is_used', 'created_at', 'expires_at', 'used_at')
    list_filter = ('is_used', 'created_at', 'expires_at', 'used_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at', 'expires_at', 'used_at')
    list_per_page = 25
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def get_readonly_fields(self, request, obj=None):
        # Tous les champs sont en lecture seule sauf is_used
        if obj:  # Si on édite un objet existant
            return ('user', 'points', 'token', 'created_at', 'expires_at', 'used_at')
        return ('token', 'created_at', 'expires_at', 'used_at')
