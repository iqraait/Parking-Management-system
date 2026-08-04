from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Permissions', {'fields': ('role', 'can_view_dashboard', 'can_manage_entry', 'can_manage_exit', 'can_manage_payments', 'can_view_reports', 'can_search', 'can_manage_zones', 'can_manage_settings')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Configuration', {'fields': ('role',)}),
    )

admin.site.register(User, CustomUserAdmin)
