import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parkos.settings')
django.setup()

from django.test import Client
from accounts.models import User
from parking.models import VehicleRecord

# Create test client
c = Client()
user = User.objects.first()
if user:
    c.force_login(user)

veh = VehicleRecord.objects.filter(status='ACTIVE').first()
if veh:
    print(f"Executing exit for {veh.ticket_number}")
    response = c.post('/exit/', {'ticket_number': veh.ticket_number})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 500:
        print("INTERNAL SERVER ERROR")
else:
    print("No active vehicles found")
