from django.contrib import admin
from apps.account.models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'u_id', 'email', 'role', 'date_joined']
    list_display_links = ['id', 'u_id']

admin.site.register(User, UserAdmin)
