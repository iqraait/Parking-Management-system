from django.contrib import admin
from .models import ParkingZone, VehicleRecord

@admin.register(ParkingZone)
class ParkingZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'capacity', 'base_hourly_price', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)

@admin.register(VehicleRecord)
class VehicleRecordAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'vehicle_number', 'zone', 'status', 'entry_time', 'exit_time')
    search_fields = ('ticket_number', 'vehicle_number', 'driver_name')
    list_filter = ('status', 'zone')
