from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('action', 'user__username')
