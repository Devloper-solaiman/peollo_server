from django.conf import settings
from django.urls import reverse
from django.core.mail import send_mail
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_str, smart_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from rest_framework import serializers, status
from rest_framework.response import Response
from apps.account.models import User
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from apps.account.utils import Google, register_social_user, send_normal_email
from django.urls import reverse
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import ValidationError


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=50, min_length=6, write_only=True)
    confirm_password = serializers.CharField(max_length=50, min_length=6, write_only=True)

    class Meta:
        model = User
        extra_kwargs = {
                        'first_name': {'required': False},
                        'last_name': {'required': False},
                        'role': {'required': False},
                        'photo': {'required': False},
                        'credit': {'required': False},
                        'is_basic': {'required': False},
                        'is_professional': {'required': False},
                        'is_custom': {'required': False},
                        'is_blocked': {'required': False},
                        'subscribed_at': {'required': False},
                        'auth_provider': {'required': False}
                        }
        fields = [
                 'id', 'u_id', 'first_name', 'last_name', 
                 'email', 'role', 'photo',
                 'credit', 'is_basic', 'is_professional',
                 'is_custom', 'is_blocked', 
                 'password', 'confirm_password', 
                 'subscribed_at', 'date_joined', 'updated_at'
                 ]
        
    def validate(self, attrs):
        if attrs['password'] != attrs["confirm_password"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        email_exists = User.objects.filter(email=attrs["email"]).exists()

        if email_exists:
            raise serializers.ValidationError("Email has already been used")

        return super().validate(attrs)
    
    def save(self, validated_data):
        user = User.objects.create(
            email=validated_data['email']
        )
        user.is_active = False
        user.set_password(validated_data['password'])
        return user
    

class GoogleSignInSerializer(serializers.Serializer):
    access_token = serializers.CharField(min_length=6)

    def validate(self, access_token):
        print("serializer er validate function er modde")
        google_user_data = Google.validate(access_token)
        print("google_user_data", google_user_data)
        try:
            user_id = google_user_data["sub"]
            print("serializer er modde user id", user_id)
        except:
            print("error Khai boshe achi")
            raise serializers.ValidationError("This token is invalid or has expired")
        
        if google_user_data["aud"] != settings.GOOGLE_CLIENT_ID:
            raise AuthenticationFailed(detail="Couldn't verify user")
        
        email = google_user_data["email"]
        first_name = google_user_data["given_name"]
        last_name = google_user_data["family_name"]
        provider = "google"

        return register_social_user(provider, email, first_name, last_name)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=68, write_only=True)
    access_token = serializers.CharField(max_length=255, read_only=True)
    refresh_token = serializers.CharField(max_length=255, read_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        request = self.context.get('request')
        user = authenticate(request=request, email=email, password=password)
        if not user:
            raise AuthenticationFailed("Invalid credentials, please try again.")
        if not user.is_active:
            raise AuthenticationFailed("Email is not verified.")
        
        # Make sure `tokens()` method exists on the user and returns the required tokens
        user_tokens = user.tokens() if hasattr(user, 'tokens') else None
        if user_tokens is None or 'access_token' not in user_tokens or 'refresh' not in user_tokens:
            raise AuthenticationFailed("Unable to retrieve tokens for the user.")
        
        return {
            'email': user.email,
            "access_token": user_tokens.get("access_token"),
            "refresh_token": user_tokens.get("refresh")
        }
    

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        print(value)
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist")
        return value
    

class SetNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid token or user ID.")

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError("Invalid token.")
        
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value
    
    def validate(self, attrs):
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError("New Password cannot be the same as the old password")
        
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
                  'id', 'first_name', 'last_name', 'title',
                  'email', 'photo', 'credit', "is_basic", 
                  "is_professional", "is_custom", 'auth_provider'
                  ]
        
      
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
                  'id', 'first_name', 'last_name', 
                  'title', 'email', 'photo'
                  ]
        
    def update(self, instance, validated_data):
        new_email = validated_data.get("email", instance.email)
        email_change = False

        if instance.email != new_email:
            email_change = True
            token = default_token_generator.make_token(instance)
            user_id = instance.id

            cache.set(f"email_change_{user_id}", new_email, timeout=300)
            cache.set(f"email_change_token_{user_id}", token, timeout=300)

            verification_link = self.context['request'].build_absolute_uri(
                reverse('verify-email-change', kwargs={'user_id': user_id, 'token': token})
            )

            send_mail(
                'Verify your new email address',
                f"Click the link to verify your new email address: {verification_link}",
                settings.DEFAULT_FROM_EMAIL,
                [new_email]
            )

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.title = validated_data.get('title', instance.title)
        instance.photo = validated_data.get('photo', instance.photo)
        
        instance.save()
        self.context['email_changed'] = email_change
        return instance
        
        
class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        extra_kwargs = {
                        'photo': {'required': False},
                        'first_name': {'required': False},
                        'last_name': {'required': False},
                        'role': {'required': False},
                        'is_basic': {'required': False},
                        'is_professional': {'required': False},
                        'is_custom': {'required': False},
                        'is_staff': {'required': False},
                        'is_blocked': {'required': False},
                        'email': {'required': False},
                        'credit': {'required': False}
                        }
        fields = [
                  'id', 'first_name', 'last_name',
                  'role', 'is_active', 'is_staff',
                  'is_basic', 'is_professional', 'credit',
                  'is_custom', 'is_blocked', 'email'
                  ]
        

class AllUsersSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
                  'id', 'first_name', 'email',
                  'role', 'is_basic', 'is_professional',
                  'is_custom', 'is_blocked', 'credit'
                 ]