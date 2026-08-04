from django.db import models
from accounts.models import User
from django.utils import timezone

class ParkingZone(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField(default=50)
    vehicle_types = models.CharField(max_length=200, help_text="Comma separated types, e.g. Car,Bike,Truck")
    base_hourly_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for first base hours")
    additional_hour_after = models.PositiveIntegerField(default=1, help_text="Apply additional price after X hours")
    extra_hours_step = models.PositiveIntegerField(default=1, help_text="Charge applies per every X extra hours")
    additional_hour_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_free = models.BooleanField(default=False, help_text="If checked, zone is 100% free")
    assigned_staff = models.ManyToManyField(User, limit_choices_to={'role': 'Staff'}, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def current_occupancy(self):
        return self.vehiclerecord_set.filter(status='ACTIVE').count()
    
    def available_slots(self):
        return max(0, self.capacity - self.current_occupancy())

    def __str__(self):
        return f"{self.name} ({self.code})"

class VehicleRecord(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('EXITED', 'Exited'),
    )
    
    ticket_number = models.CharField(max_length=50, unique=True)
    zone = models.ForeignKey(ParkingZone, on_delete=models.PROTECT)
    vehicle_number = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=50)
    driver_name = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    notes = models.TextField(blank=True)
    # entry_photo = models.ImageField(upload_to='entry_photos/', blank=True, null=True)

    entry_time = models.DateTimeField(default=timezone.now)
    entry_staff = models.ForeignKey(User, related_name='entries_managed', on_delete=models.SET_NULL, null=True)
    
    exit_time = models.DateTimeField(blank=True, null=True)
    exit_staff = models.ForeignKey(User, related_name='exits_managed', on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    duration_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_current_charges(self):
        if self.zone.is_free:
            return 0
            
        now = self.exit_time if self.exit_time else timezone.now()
        duration_seconds = (now - self.entry_time).total_seconds()
        hours = duration_seconds / 3600.0
        if hours <= 0:
            return 0
        
        # apply pricing
        zone = self.zone
        charge = float(zone.base_hourly_price)
        
        # User requested: only when car *reaches* the extra hour block does it trigger, so we use math.floor
        if hours > float(zone.additional_hour_after):
            import math
            extra_time = hours - float(zone.additional_hour_after)
            extra_blocks = math.floor(extra_time / float(zone.extra_hours_step))
            
            # Since math.floor ignores partials, if they want exact match triggers we add them
            if extra_blocks > 0:
                charge += extra_blocks * float(zone.additional_hour_price)
                
            # Edge case buffer: if the strict user example meant something else, floor mostly handles "no partial charge"
            
        return round(charge, 2)

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            import uuid
            self.ticket_number = str(uuid.uuid4().hex[:8]).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} - {self.vehicle_number}"
