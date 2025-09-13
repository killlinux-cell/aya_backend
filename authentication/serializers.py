from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile, PasswordResetToken, Vendor
from django.utils import timezone
from datetime import timedelta
import uuid


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription d'un nouvel utilisateur
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password_confirm')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # Créer automatiquement le profil utilisateur
        UserProfile.objects.create(
            user=user,
            phone_number='',
            notifications_enabled=True,
            email_notifications=True
        )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion utilisateur
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Email ou mot de passe incorrect.')
            if not user.is_active:
                raise serializers.ValidationError('Ce compte a été désactivé.')
            
            # Mettre à jour la dernière connexion
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Email et mot de passe requis.')


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil utilisateur
    """
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'available_points', 'exchanged_points', 'collected_qr_codes',
            'personal_qr_code', 'created_at', 'last_login_at'
        )
        read_only_fields = ('id', 'email', 'personal_qr_code', 'created_at', 'last_login_at')


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la mise à jour du profil utilisateur
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name')
    
    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer pour le changement de mot de passe
    """
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Ancien mot de passe incorrect.')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer pour la demande de réinitialisation de mot de passe
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError('Ce compte a été désactivé.')
        except User.DoesNotExist:
            # Ne pas révéler si l'email existe ou non
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer pour la confirmation de réinitialisation de mot de passe
    """
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate_token(self, value):
        try:
            reset_token = PasswordResetToken.objects.get(token=value)
            if not reset_token.is_valid():
                raise serializers.ValidationError('Token invalide ou expiré.')
            self.reset_token = reset_token
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError('Token invalide.')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs
    
    def save(self):
        user = self.reset_token.user
        user.set_password(self.validated_data['new_password'])
        user.save()
        
        # Marquer le token comme utilisé
        self.reset_token.is_used = True
        self.reset_token.save()
        
        return user


class UserProfileExtendedSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil étendu de l'utilisateur
    """
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = (
            'user', 'phone_number', 'date_of_birth', 'profile_picture',
            'bio', 'notifications_enabled', 'email_notifications', 'updated_at'
        )
        read_only_fields = ('updated_at',)


class VendorSerializer(serializers.ModelSerializer):
    """
    Serializer pour les informations des vendeurs
    """
    full_name = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'vendor_code', 'business_name', 'business_address',
            'phone_number', 'status', 'full_name', 'is_active',
            'user_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VendorLoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion des vendeurs
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Authentifier l'utilisateur
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Identifiants invalides')
            
            # Vérifier que l'utilisateur est un vendeur
            try:
                vendor = Vendor.objects.get(user=user)
                if not vendor.is_active:
                    raise serializers.ValidationError('Compte vendeur inactif')
                attrs['user'] = user
                attrs['vendor'] = vendor
            except Vendor.DoesNotExist:
                raise serializers.ValidationError('Ce compte n\'est pas autorisé comme vendeur')
        else:
            raise serializers.ValidationError('Email et mot de passe requis')
        
        return attrs


class ClientInfoSerializer(serializers.ModelSerializer):
    """
    Serializer pour exposer les informations client nécessaires pour les reçus
    """
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 'date_joined')
        read_only_fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 'date_joined')
    
    def get_full_name(self, obj):
        """Retourne le nom complet du client"""
        return f"{obj.first_name} {obj.last_name}".strip()
