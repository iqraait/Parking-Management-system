from django.db import models
from parking.models import VehicleRecord
from accounts.models import User

class PaymentMethod(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Payment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    
    vehicle_record = models.OneToOneField(VehicleRecord, on_delete=models.CASCADE, related_name='payment')
    method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment {self.id} for {self.vehicle_record.ticket_number}"
