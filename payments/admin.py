from django.contrib import admin
from .models import PaymentMethod, Payment

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('vehicle_record', 'method', 'amount', 'status', 'processed_at')
    list_filter = ('status', 'method')
