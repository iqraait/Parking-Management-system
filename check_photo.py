import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')
django.setup()

from parking.models import VehicleRecord

record = VehicleRecord.objects.filter(ticket_number__icontains='A161E73C').first()
if record:
    print(f"ID: {record.ticket_number}")
    print(f"Photo path: {record.entry_photo}")
    if record.entry_photo:
        print(f"File exists: {os.path.exists(record.entry_photo.path)}")
else:
    print("Record not found")
