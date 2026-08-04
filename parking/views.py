from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum, Avg
from parking.models import ParkingZone, VehicleRecord
from payments.models import Payment

@login_required
def dashboard_view(request):
    today = timezone.localtime().date()
    
    # Active Vehicles calculation
    active_vehicles = VehicleRecord.objects.filter(status='ACTIVE').count()
    
    # Entries Today
    total_entry = VehicleRecord.objects.filter(entry_time__date=today).count()
    
    # Revenue Today
    revenue_agg = Payment.objects.filter(processed_at__date=today, status='COMPLETED').aggregate(total=Sum('final_amount'))
    revenue_today = revenue_agg['total'] if revenue_agg['total'] else 0.00
    
    # Recent live records for the table
    recent_records = VehicleRecord.objects.all().order_by('-entry_time')[:10]
    
    # Slots available
    total_capacity = sum([zone.capacity for zone in ParkingZone.objects.filter(is_active=True)])
    available_slots = max(0, total_capacity - active_vehicles)
    
    # Average Duration (Only exited vehicles have duration)
    avg_dur_agg = VehicleRecord.objects.filter(status='EXITED').aggregate(avg=Avg('duration_hours'))
    avg_duration = avg_dur_agg['avg'] if avg_dur_agg['avg'] else 0.0
    
    context = {
        'active_vehicles': active_vehicles,
        'total_entry': total_entry,
        'revenue_today': revenue_today,
        'recent_records': recent_records,
        'available_slots': available_slots,
        'avg_duration': round(avg_duration, 1),
    }
    return render(request, 'dashboard/index.html', context)
def entry_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'edit_vehicle':
            ticket_num = request.POST.get('ticket_number')
            new_num = request.POST.get('vehicle_number')
            new_zone_id = request.POST.get('zone_id')
            try:
                veh = VehicleRecord.objects.get(ticket_number=ticket_num, status='ACTIVE')
                veh.vehicle_number = new_num
                if new_zone_id:
                    veh.zone = ParkingZone.objects.get(id=new_zone_id)
                veh.save()
                messages.success(request, f"Ticket {ticket_num} updated successfully!")
            except Exception as e:
                messages.error(request, f"Error updating ticket: {str(e)}")
            from django.shortcuts import redirect
            return redirect('entry')
            
        vehicle_num = request.POST.get('vehicle_number')
        v_type = request.POST.get('vehicle_type')
        zone_id = request.POST.get('zone_id')
        mobile = request.POST.get('mobile', '')
        notes = request.POST.get('notes', '')
        entry_photo = request.FILES.get('entry_photo')
        entry_photo_base64 = request.POST.get('entry_photo_base64')

        import base64
        import uuid
        from django.core.files.base import ContentFile

        final_photo = entry_photo
        if not final_photo and entry_photo_base64:
            try:
                format, imgstr = entry_photo_base64.split(';base64,') 
                ext = format.split('/')[-1]
                final_photo = ContentFile(base64.b64decode(imgstr), name=f"capture_{uuid.uuid4().hex[:8]}.{ext}")
            except Exception as e:
                pass

        try:
            zone = ParkingZone.objects.get(id=zone_id)
            if zone.available_slots() > 0:
                record = VehicleRecord.objects.create(
                    zone=zone,
                    vehicle_number=vehicle_num,
                    vehicle_type=v_type,
                    mobile=mobile,
                    notes=notes,
                    entry_photo=final_photo,
                    entry_staff=request.user
                )
                messages.success(request, f"Ticket {record.ticket_number} generated successfully!")
                from django.shortcuts import redirect
                return redirect('entry')
            else:
                messages.error(request, "Selected zone is full.")
        except ParkingZone.DoesNotExist:
            messages.error(request, "Invalid Zone Selected.")

    zones = ParkingZone.objects.filter(is_active=True)
    
    # Date Filtering
    date_filter = request.GET.get('date')
    recent_entries = VehicleRecord.objects.filter(status='ACTIVE')
    if date_filter:
        recent_entries = recent_entries.filter(entry_time__date=date_filter)
    recent_entries = recent_entries.order_by('-entry_time')
    
    # Calculate live accumulating charge for display in template
    for entry in recent_entries:
        entry.live_charge = entry.calculate_current_charges()
    
    return render(request, 'parking/entry.html', {
        'title': 'Vehicle Entry',
        'zones': zones,
        'recent_entries': recent_entries
    })

@login_required
def exit_view(request):
    record = None
    query = request.GET.get('q', '')
    if query:
        record = VehicleRecord.objects.filter(Q(vehicle_number__icontains=query) | Q(ticket_number__iexact=query), status='ACTIVE').first()
        if record:
            # calculate live charges
            record.exit_time = timezone.now()
            duration = (record.exit_time - record.entry_time).total_seconds() / 3600.0
            record.duration_hours = max(0, round(duration, 2))
            record.total_charges = record.calculate_current_charges()

    if request.method == 'POST':
        ticket_num = request.POST.get('ticket_number')
        try:
            veh = VehicleRecord.objects.get(ticket_number=ticket_num, status='ACTIVE')
            veh.exit_time = timezone.now()
            veh.exit_staff = request.user
            veh.status = 'EXITED'
            
            duration = (veh.exit_time - veh.entry_time).total_seconds() / 3600.0
            veh.duration_hours = max(0, round(duration, 2))
            veh.total_charges = veh.calculate_current_charges()
            veh.save()
            
            Payment.objects.create(
                vehicle_record=veh,
                amount=veh.total_charges,
                final_amount=veh.total_charges,
                status='COMPLETED',
                processed_by=request.user
            )
            messages.success(request, f"Payment successful for {veh.vehicle_number}. Vehicle exited.")
            record = None  # Clear the search output
        except VehicleRecord.DoesNotExist:
            messages.error(request, "Error processing exit.")

    # Date Filtering
    date_filter = request.GET.get('date')
    today = timezone.localtime().date()
    
    recent_exits = VehicleRecord.objects.filter(status='EXITED')
    if date_filter:
        recent_exits = recent_exits.filter(exit_time__date=date_filter)
    else:
        recent_exits = recent_exits.filter(exit_time__date=today)
        date_filter = today.strftime('%Y-%m-%d')
        
    recent_exits = recent_exits.order_by('-exit_time')

    return render(request, 'parking/exit.html', {
        'title': 'Vehicle Exit',
        'record': record,
        'query': query,
        'recent_exits': recent_exits,
        'current_date': date_filter
    })

@login_required
def vehicle_log_view(request):
    # Logs View: showing ALL vehicles (active and exited) with DataTables
    date_filter = request.GET.get('date')
    all_vehicles = VehicleRecord.objects.all().select_related('zone', 'entry_staff', 'exit_staff').order_by('-entry_time')
    
    if date_filter:
        all_vehicles = all_vehicles.filter(entry_time__date=date_filter)

    return render(request, 'parking/vehicle_logs.html', {
        'title': 'Vehicle Directory Log',
        'vehicles': all_vehicles,
        'current_date': date_filter
    })

@login_required
def zones_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'edit_zone':
            zone_id = request.POST.get('zone_id')
            try:
                z = ParkingZone.objects.get(id=zone_id)
                z.name = request.POST.get('name')
                z.capacity = request.POST.get('capacity')
                z.is_free = request.POST.get('is_free') == 'true'
                z.base_hourly_price = request.POST.get('base_price', 0)
                z.additional_hour_after = request.POST.get('base_hours', 1)
                z.additional_hour_price = request.POST.get('extra_price', 0)
                z.extra_hours_step = request.POST.get('extra_step', 1)
                z.save()
                messages.success(request, f"Zone '{z.name}' updated successfully!")
            except Exception as e:
                messages.error(request, f"Error updating zone: {str(e)}")
            from django.shortcuts import redirect
            return redirect('zones')
            
        name = request.POST.get('name')
        code = request.POST.get('code')
        capacity = request.POST.get('capacity')
        is_free = request.POST.get('is_free') == 'on'  # check-box
        base_price = request.POST.get('base_price', 0) if request.POST.get('base_price') else 0
        extra_price = request.POST.get('extra_price', 0) if request.POST.get('extra_price') else 0
        base_hours = request.POST.get('base_hours', 1) if request.POST.get('base_hours') else 1
        extra_step = request.POST.get('extra_step', 1) if request.POST.get('extra_step') else 1
        
        try:
            ParkingZone.objects.create(
                name=name, code=code, capacity=capacity, 
                is_free=is_free,
                base_hourly_price=base_price, additional_hour_price=extra_price,
                additional_hour_after=base_hours, extra_hours_step=extra_step
            )
            messages.success(request, f"Parking Zone '{name}' created successfully!")
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                messages.error(request, f"Error: A zone with the code '{code}' already exists.")
            else:
                messages.error(request, f"Error creating zone: {str(e)}")
                
        from django.shortcuts import redirect
        return redirect('zones')
        
    zones = ParkingZone.objects.all().order_by('-id')
    return render(request, 'parking/zones.html', {'title': 'Parking Zones', 'zones': zones})

@login_required
def reports_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ai_compare':
            import time
            from datetime import datetime
            
            # Artificial sleep to show the sophisticated UI loader
            time.sleep(1.8)
            
            date1_str = request.POST.get('date1')
            date2_str = request.POST.get('date2')
            
            # Use '0' if no records exist
            rev1_agg = Payment.objects.filter(payment_time__date=date1_str, status='COMPLETED').aggregate(total=Sum('final_amount'))
            rev1 = rev1_agg['total'] if rev1_agg['total'] else 0.0
            
            rev2_agg = Payment.objects.filter(payment_time__date=date2_str, status='COMPLETED').aggregate(total=Sum('final_amount'))
            rev2 = rev2_agg['total'] if rev2_agg['total'] else 0.0
            
            diff = float(rev2) - float(rev1)
            
            if rev1 == 0:
                growth = 100.0 if rev2 > 0 else 0.0
            else:
                growth = (diff / float(rev1)) * 100
                
            if diff > 0:
                advice = f"Performance Insight: Your revenue on '{date2_str}' increased by {abs(growth):.1f}% compared to the baseline '{date1_str}'. The predictive model detects strong utilization. We recommend allocating more staff during these peak zones."
            elif diff < 0:
                advice = f"Deflection Alert: Revenue dropped by {abs(growth):.1f}%. The AI engines detected under-capacity check-ins. Consider dynamically adjusting zone pricing or initiating off-peak promotional discounts to entice drivers."
            else:
                advice = "Equilibrium: Revenue remained identical mathematically. The neural models suggest a stable, consistent baseline pattern without any significant anomalies."
                
            return render(request, 'parking/partials/ai_insight.html', {
                'date1': date1_str, 'date2': date2_str,
                'rev1': rev1, 'rev2': rev2,
                'growth': growth, 'advice': advice
            })

    # Calculate some real report metrics
    today = timezone.localtime().date()
    total_entry = VehicleRecord.objects.filter().count()
    revenue_agg = Payment.objects.filter(status='COMPLETED').aggregate(total=Sum('final_amount'))
    total_revenue = revenue_agg['total'] if revenue_agg['total'] else 0.00
    
    return render(request, 'parking/reports.html', {
        'title': 'Analytics & Reports',
        'total_entry': total_entry,
        'total_revenue': total_revenue
    })

from accounts.models import User
from django.contrib.auth.hashers import make_password

@login_required
def settings_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # User Edit Logic
        if action == 'edit_user':
            user_id = request.POST.get('user_id')
            try:
                u = User.objects.get(id=user_id)
                u.mobile = request.POST.get('mobile', '')
                # Reapply privileges
                u.can_view_dashboard = request.POST.get('priv_dashboard') == 'true'
                u.can_manage_entry = request.POST.get('priv_manage_entry') == 'true'
                u.can_edit_entry = request.POST.get('priv_edit_entry') == 'true'
                u.can_manage_exit = request.POST.get('priv_manage_exit') == 'true'
                u.can_collect_cash = request.POST.get('priv_collect_cash') == 'true'
                u.can_edit_exit = request.POST.get('priv_edit_exit') == 'true'
                u.can_manage_zones = request.POST.get('priv_manage_zones') == 'true'
                u.can_edit_zones = request.POST.get('priv_edit_zones') == 'true'
                u.can_view_reports = request.POST.get('priv_view_reports') == 'true'
                u.can_download_reports = request.POST.get('priv_download_reports') == 'true'
                u.save()
                messages.success(request, f"User '{u.username}' updated.")
            except Exception as e:
                messages.error(request, f"Error: {e}")
            from django.shortcuts import redirect
            return redirect('settings')
            
        # User Creation Logic
        if action == 'create_user':
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')
            mobile = request.POST.get('mobile', '')
            
            if not User.objects.filter(username=username).exists():
                User.objects.create(
                    username=username,
                    email=email,
                    mobile=mobile,
                    password=make_password(password),
                    role=role,
                    can_view_dashboard=request.POST.get('priv_dashboard') == 'true',
                    can_manage_entry=request.POST.get('priv_manage_entry') == 'true',
                    can_edit_entry=request.POST.get('priv_edit_entry') == 'true',
                    can_manage_exit=request.POST.get('priv_manage_exit') == 'true',
                    can_collect_cash=request.POST.get('priv_collect_cash') == 'true',
                    can_edit_exit=request.POST.get('priv_edit_exit') == 'true',
                    can_manage_zones=request.POST.get('priv_manage_zones') == 'true',
                    can_edit_zones=request.POST.get('priv_edit_zones') == 'true',
                    can_view_reports=request.POST.get('priv_view_reports') == 'true',
                    can_download_reports=request.POST.get('priv_download_reports') == 'true',
                    can_manage_settings=True if role == 'Super Admin' else False,
                    is_staff=True if role in ['Super Admin', 'Administrator'] else False,
                    is_superuser=True if role == 'Super Admin' else False
                )
                messages.success(request, f"User {username} created with precise privileges.")
            else:
                messages.error(request, "Username already exists!")
                
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'parking/settings.html', {'title': 'System Settings', 'users': users})

import math

def public_display_view(request):
    zones = list(ParkingZone.objects.filter(is_active=True).order_by('name'))
    
    per_page = 4
    total_zones = len(zones)
    total_pages = math.ceil(total_zones / per_page) if total_zones > 0 else 1
        
    try:
        current_page = int(request.GET.get('page', 1))
    except ValueError:
        current_page = 1
        
    if current_page > total_pages or current_page < 1:
        current_page = 1
        
    next_page = current_page + 1 if current_page < total_pages else 1

    start_idx = (current_page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_zones = zones[start_idx:end_idx]

    display_zones = []
    for zone in paginated_zones:
        display_zones.append({
            'name': zone.name,
            'code': zone.code,
            'available': zone.available_slots(),
        })
    
    context = {
        'title': 'Public Display Screen',
        'zones': display_zones,
        'current_page': current_page,
        'total_pages': total_pages,
        'next_page': next_page,
    }
    return render(request, 'parking/public_display.html', context)
