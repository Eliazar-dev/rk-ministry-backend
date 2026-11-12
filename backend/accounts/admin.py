from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmailOTP, User


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'purpose', 'attempts', 'created')
    readonly_fields = ('email', 'purpose', 'code_hash', 'name', 'password_hash', 'attempts', 'created')


@admin.register(User)
class MemberAdmin(UserAdmin):
    ordering = ('-date_joined',)
    list_display = ('email', 'first_name', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Profile', {'fields': ('first_name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'first_name', 'password1', 'password2')}),
    )
