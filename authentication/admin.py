from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, PasswordResetToken, Vendor
from .models_grand_prix import GrandPrix, GrandPrixPrize, GrandPrixParticipation, GrandPrixDraw

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'available_points', 'exchanged_points', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name')}),
        ('Points et QR Code', {'fields': ('available_points', 'exchanged_points', 'collected_qr_codes', 'personal_qr_code')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'notifications_enabled', 'updated_at')
    list_filter = ('notifications_enabled', 'email_notifications', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone_number')
    readonly_fields = ('updated_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        'business_name', 
        'vendor_code', 
        'user_email', 
        'status', 
        'city', 
        'country', 
        'created_at',
        'is_active_display'
    )
    list_filter = (
        'status', 
        'country', 
        'city', 
        'created_at',
        'updated_at'
    )
    search_fields = (
        'business_name', 
        'vendor_code', 
        'user__email', 
        'user__first_name', 
        'user__last_name',
        'phone_number',
        'city',
        'region'
    )
    readonly_fields = (
        'vendor_code', 
        'created_at', 
        'updated_at',
        'is_active_display'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'user', 
                'vendor_code', 
                'business_name', 
                'status',
                'is_active_display'
            )
        }),
        ('Contact', {
            'fields': (
                'phone_number', 
                'business_address'
            )
        }),
        ('Localisation', {
            'fields': (
                'latitude', 
                'longitude', 
                'city', 
                'region', 
                'country'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'created_by', 
                'created_at', 
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def is_active_display(self, obj):
        return obj.is_active
    is_active_display.short_description = 'Actif'
    is_active_display.boolean = True
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau vendeur
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_vendors', 'deactivate_vendors', 'suspend_vendors']
    
    def activate_vendors(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} vendeur(s) activé(s) avec succès.')
    activate_vendors.short_description = "Activer les vendeurs sélectionnés"
    
    def deactivate_vendors(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} vendeur(s) désactivé(s) avec succès.')
    deactivate_vendors.short_description = "Désactiver les vendeurs sélectionnés"
    
    def suspend_vendors(self, request, queryset):
        updated = queryset.update(status='suspended')
        self.message_user(request, f'{updated} vendeur(s) suspendu(s) avec succès.')
    suspend_vendors.short_description = "Suspendre les vendeurs sélectionnés"


@admin.register(GrandPrix)
class GrandPrixAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'status', 
        'participation_cost', 
        'start_date', 
        'end_date', 
        'draw_date',
        'participants_count',
        'winners_count'
    )
    list_filter = ('status', 'start_date', 'end_date', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-start_date',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'name', 
                'description', 
                'participation_cost',
                'status'
            )
        }),
        ('Période', {
            'fields': (
                'start_date', 
                'end_date', 
                'draw_date'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'created_by', 
                'created_at', 
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def participants_count(self, obj):
        return obj.participations.count()
    participants_count.short_description = 'Participants'
    
    def winners_count(self, obj):
        return obj.participations.filter(is_winner=True).count()
    winners_count.short_description = 'Gagnants'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(GrandPrixPrize)
class GrandPrixPrizeAdmin(admin.ModelAdmin):
    list_display = ('grand_prix', 'position', 'name', 'value')
    list_filter = ('grand_prix', 'position')
    search_fields = ('name', 'description', 'grand_prix__name')
    ordering = ('grand_prix', 'position')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('grand_prix')


@admin.register(GrandPrixParticipation)
class GrandPrixParticipationAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 
        'grand_prix_name', 
        'points_spent', 
        'is_winner', 
        'prize_won_name',
        'participated_at'
    )
    list_filter = ('is_winner', 'participated_at', 'grand_prix', 'prize_won')
    search_fields = (
        'user__email', 
        'user__first_name', 
        'user__last_name',
        'grand_prix__name'
    )
    readonly_fields = ('participated_at', 'notified_at')
    ordering = ('-participated_at',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def grand_prix_name(self, obj):
        return obj.grand_prix.name
    grand_prix_name.short_description = 'Grand Prix'
    grand_prix_name.admin_order_field = 'grand_prix__name'
    
    def prize_won_name(self, obj):
        return obj.prize_won.name if obj.prize_won else 'N/A'
    prize_won_name.short_description = 'Récompense gagnée'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'grand_prix', 'prize_won')


@admin.register(GrandPrixDraw)
class GrandPrixDrawAdmin(admin.ModelAdmin):
    list_display = ('grand_prix_name', 'winners_count', 'drawn_at', 'drawn_by_email')
    list_filter = ('drawn_at', 'grand_prix')
    search_fields = ('grand_prix__name', 'drawn_by__email')
    readonly_fields = ('drawn_at',)
    ordering = ('-drawn_at',)
    
    def grand_prix_name(self, obj):
        return obj.grand_prix.name
    grand_prix_name.short_description = 'Grand Prix'
    grand_prix_name.admin_order_field = 'grand_prix__name'
    
    def winners_count(self, obj):
        return obj.winners.count()
    winners_count.short_description = 'Nombre de gagnants'
    
    def drawn_by_email(self, obj):
        return obj.drawn_by.email if obj.drawn_by else 'N/A'
    drawn_by_email.short_description = 'Effectué par'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('grand_prix', 'drawn_by')