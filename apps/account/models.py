import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.account.managers import CustomUserManager
from rest_framework_simplejwt.tokens import RefreshToken

AUTH_PROVIDERS = {"email": 'email', 'google': 'google'}


class User(AbstractBaseUser, PermissionsMixin):
    class ROLE_TYPE(models.TextChoices):
        USER = 'USER', 'User'
        ADMIN = 'ADMIN', 'Admin'
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super_Admin'

    u_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    role = models.CharField(max_length=80, choices=ROLE_TYPE.choices, default=ROLE_TYPE.USER)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(unique=True)
    title = models.CharField(max_length=50, blank=True, null=True)
    photo = models.ImageField(upload_to='account/photo/', blank=True)
    credit = models.FloatField(default=0.0)
    is_basic = models.BooleanField(default=False)
    is_professional = models.BooleanField(default=False)
    is_custom = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    subscribed_at = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    auth_provider =models.CharField(max_length=50, default=AUTH_PROVIDERS.get('email'))

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        access = refresh.access_token
        access['role'] = self.role
        return {
            "refresh": str(refresh),
            "access_token": str(access)
        }


class OneTimePassword(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    code = models.CharField(max_length=6, unique=True)

    def __str__(self):
        return f"Pass-code{self.code}"