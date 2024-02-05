

import os
import cv2
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings  
import qrcode
from pyzbar.pyzbar import decode
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import numpy as np
import base64
from io import BytesIO
from myapp.models import TemporaryAttendance
from myapp.models import Archive
from django.utils import timezone
from datetime import timedelta,datetime,date
from myapp.models import qr_existing_list
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.messages import get_messages






def fetch_messages(request):
    # Retrieve messages based on tags (e.g., 'timein', 'breakout')
    messages = get_messages(request)
    filtered_messages = [
        {'text': message.message, 'tags': message.tags} for message in messages if 'timein' in message.tags 
        or 'breakout' in message.tags or 'breakin' in message.tags or 'timeout' in message.tags
        or 'no_bibo' in message.tags or 'breakin_aft' in message.tags or 'timeout_aft' in message.tags
        or 'timein_already' in message.tags or 'breakin_already' in message.tags or 'timeout_already' in message.tags
    ]

    return JsonResponse({'messages': filtered_messages})

    
@csrf_exempt
def webcam_qr_code_scanner(request):
    if request.method == 'POST':
        image_data = request.FILES['webcam_image'].read()
        decoded_objects = scan_qr_code_from_image_data(image_data)
        current_time = datetime.now()

        if decoded_objects:
            # QR code scanned successfully
            name = decoded_objects[0].data.decode('utf-8')
            prac_time = current_time.strftime("%H:%M")
            qr_existing = qr_existing_list.objects.filter(employee_unique_id=name).first()
            formatted_name = f"{qr_existing.fn} {qr_existing.ln}" if qr_existing else name
            
            if "06:00" <= prac_time <= "08:00":
                deleteTable()
            
            # FOR TIMEIN
            if "03:00" <= prac_time <= "10:59":
                existing_entry = TemporaryAttendance.objects.filter(name=formatted_name,date=current_time.date()).first()
                if existing_entry is None:
                    insertData(name, current_time,request)
                    #Archive.objects.filter(name=name,date=current_time.date()).create(name=formatted_name,timein_names=name,timein_timestamps=current_time)
                    messages.success(request, f'Timein Successfully! - {formatted_name}', extra_tags='timein')
                    return HttpResponseRedirect(request.path)
                
                timein_already = Archive.objects.filter(name=formatted_name, date=current_time.date()).first()
                existing_entry_timein_timestamps = timein_already.timein_timestamps.replace(tzinfo=timezone.utc)
                current_time = current_time.replace(tzinfo=timezone.utc)

                if current_time - existing_entry_timein_timestamps >= timedelta(seconds=4):
                    messages.success(request, f'Timein Already! - {formatted_name}', extra_tags='timein_already')
                    return HttpResponseRedirect(request.path)
                
            # FOR BREAKOUT
            if "12:00" <= prac_time <= "13:00" and Archive.objects.filter(name=formatted_name, timein_names__isnull=False, breakout_names__isnull=True, date=current_time.date()).exists():
                existing_entry = Archive.objects.filter(name=formatted_name, date=current_time.date()).first()

                existing_entry_timein_timestamps = existing_entry.timein_timestamps.replace(tzinfo=timezone.utc)
                current_time = current_time.replace(tzinfo=timezone.utc)

                time_difference = current_time - existing_entry_timein_timestamps
                remaining_seconds = max(15 - time_difference.total_seconds(), 0)

                if current_time - existing_entry_timein_timestamps >= timedelta(seconds=15):
                    breakout(name, current_time)
                    Archive.objects.filter(name=formatted_name, date=current_time.date()).update(breakout_names=formatted_name,breakout_timestamps=current_time)
                    messages.success(request, f'Breakout Successfully! - {formatted_name}', extra_tags='breakout')
                    return HttpResponseRedirect(request.path)
          
               

            # FOR BREAKIN
            if "12:00" <= prac_time <= "14:00" and Archive.objects.filter(name=formatted_name, timein_names__isnull=False, breakout_names__isnull=False,breakin_names__isnull=True, date=current_time.date()).exists():
                existing_entry2 = Archive.objects.filter(name=formatted_name, date=current_time.date()).first()
                      
                existing_entry_breakout_timestamps = existing_entry2.breakout_timestamps.replace(tzinfo=timezone.utc)
                current_time = current_time.replace(tzinfo=timezone.utc) 

                if current_time - existing_entry_breakout_timestamps >= timedelta(seconds=6):
                    breakin(name, current_time)
                    Archive.objects.filter(name=formatted_name, date=current_time.date()).update(breakin_names=formatted_name,breakin_timestamps=current_time)
                    messages.success(request, f'Breakin Successfully! - {formatted_name}', extra_tags='breakin')
                    return HttpResponseRedirect(request.path)


            # IF BREAKIN IS ALREADY INSERTED 
            if "12:00" <= prac_time <= "15:00" and Archive.objects.filter(name=formatted_name, timein_names__isnull=False,breakout_names__isnull=False,breakin_names__isnull=False,timeout_names__isnull=True,date=current_time.date()).exists():
                existing_entry3 = Archive.objects.filter(name=formatted_name, date=current_time.date()).first()

                existing_entry_breakin_timestamps = existing_entry3.breakin_timestamps.replace(tzinfo=timezone.utc)
                current_time = current_time.replace(tzinfo=timezone.utc)
                
                if current_time - existing_entry_breakin_timestamps >= timedelta(seconds=6):
                    messages.success(request, f'BREAKIN ALREADY! - {formatted_name}', extra_tags='breakin_already')
                    return HttpResponseRedirect(request.path)

      

            
                

            # FOR TIMEOUT
            if "15:00" <= prac_time <= "23:59" and Archive.objects.filter(name=formatted_name, timein_names__isnull=False, breakout_names__isnull=False,breakin_names__isnull=False, timeout_names__isnull=True,date=current_time.date()).exists():
                existing_entry3 = Archive.objects.filter(name=formatted_name, date=current_time.date()).first()

                existing_entry_breakin_timestamps = existing_entry3.breakin_timestamps.replace(tzinfo=timezone.utc)
                current_time = current_time.replace(tzinfo=timezone.utc)

                time_difference = current_time - existing_entry_breakin_timestamps
                remaining_seconds = max(30 - time_difference.total_seconds(), 0)

                if current_time - existing_entry_breakin_timestamps >= timedelta(seconds=30):
                    timeout(name, current_time)
                    Archive.objects.filter(name=formatted_name, date=current_time.date()).update(timeout_names=formatted_name,timeout_timestamps=current_time)
                    messages.success(request, f'Timeout Successfully! - {formatted_name}', extra_tags='timeout')
                    return HttpResponseRedirect(request.path)
      


            # IF NO BREAKOUT OR BREAKIN
            if "15:00" <= prac_time <= "23:59" and Archive.objects.filter(name=formatted_name, timein_names__isnull=False, breakin_names__isnull=True,breakout_names__isnull=True, date=current_time.date()).exists():
                messages.success(request, f'NO BREAKOUT OR BREAKIN! - {formatted_name}', extra_tags='no_bibo')
                return HttpResponseRedirect(request.path)

            # IF TIMEOUT IS ALREADY INSERTED
            if "15:00" <= prac_time <= "23:59" and Archive.objects.filter(name=formatted_name, timein_names__isnull=False,breakout_names__isnull=False,breakin_names__isnull=False,timeout_names__isnull=False,date=current_time.date()).exists():
                existing_entry7 = Archive.objects.filter(name=formatted_name, date=current_time.date()).first()

                existing_entry_breakin_timestamps = existing_entry7.timeout_timestamps.replace(tzinfo=timezone.utc)
                current_time = current_time.replace(tzinfo=timezone.utc)
                
                if current_time - existing_entry_breakin_timestamps >= timedelta(seconds=6):
                    messages.success(request, f'TIMEOUT ALREADY! - {formatted_name}', extra_tags='timeout_already')
                    return HttpResponseRedirect(request.path)
     
            
           
            
             

            # IF HALF DAY IN THE AFTERNOON - BREAKIN
            qr_existing = qr_existing_list.objects.filter(employee_unique_id=name).first()
            formatted_name = f"{qr_existing.fn} {qr_existing.ln}" if qr_existing else name
            if "11:00" <= prac_time <= "23:59":
                existing_entry = TemporaryAttendance.objects.filter(name=formatted_name,date=current_time.date()).first()
                if existing_entry is None:
                    afternoonBreakout(name, current_time,request)
                    messages.success(request, f'Breakin Successfully! - {formatted_name}', extra_tags='breakin_aft')
                    return HttpResponseRedirect(request.path)
                 
                # HALF DAY TIMEOUT
                if "15:00" <= prac_time <= "23:59" and Archive.objects.filter(name=formatted_name, breakin_names__isnull=False, timeout_names__isnull=True, date=current_time.date()).exists():
                    existing_entry = Archive.objects.filter(name=formatted_name, date=current_time.date()).first() 

                    existing_entry_breakin_timestamps = existing_entry.breakin_timestamps.replace(tzinfo=timezone.utc)
                    current_time = current_time.replace(tzinfo=timezone.utc)

                    time_difference = current_time - existing_entry_breakin_timestamps
                    remaining_seconds = max(15 - time_difference.total_seconds(), 0)

                    if current_time - existing_entry_breakin_timestamps >= timedelta(seconds=15):
                        afternoonTimeout(name, current_time)
                        Archive.objects.filter(name=formatted_name, date=current_time.date()).update(timeout_names=formatted_name,timeout_timestamps=current_time)
                        messages.success(request, f'Timeout Successfully! - {formatted_name}', extra_tags='timeout_aft')
                        return HttpResponseRedirect(request.path)
            
            
            
            return JsonResponse({"success": True, "name": name})

    return JsonResponse({"success": False, "error": "QR code not detected"})








def scan_qr_code_from_image_data(image_data):
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    decoded_objects = decode(gray)
    return decoded_objects




def afternoonBreakout(name,current_time,request):
    formatted_time = current_time.strftime("%I:%M:%S")
    branch_names = request.user.username
    
    qr_existing = qr_existing_list.objects.filter(employee_unique_id=name).first()
  
    
    if qr_existing is None:
        TemporaryAttendance.objects.filter(breakin__isnull=True,name=name,date=current_time.date()).create(name=name,breakin=formatted_time,branch_name=branch_names)
        Archive.objects.filter(name=name,date=current_time.date()).create(name=name,breakin_names=name,breakin_timestamps=current_time)
        
    else:
        formatted_name = f"{qr_existing.fn} {qr_existing.ln}"
        existing_entry = TemporaryAttendance.objects.filter(name=formatted_name, date=current_time.date()).first()
        
        if existing_entry is None:
            TemporaryAttendance.objects.filter(name=formatted_name,breakin__isnull=True, date=current_time.date()).create(name=formatted_name,breakin=formatted_time,branch_name=branch_names)
            Archive.objects.filter(name=name,date=current_time.date()).create(name=formatted_name,breakin_names=formatted_name,breakin_timestamps=current_time)


def afternoonTimeout(name,current_time):
    formatted_time = current_time.strftime("%I:%M:%S")
    TemporaryAttendance.objects.filter(name=name,breakin__isnull=False, date=current_time.date()).update(timeout=formatted_time)
    qr_existing = qr_existing_list.objects.filter(employee_unique_id=name).first()

    if qr_existing:
        formatted_name = f"{qr_existing.fn} {qr_existing.ln}"
        existing_entry = TemporaryAttendance.objects.filter(name=formatted_name, date=current_time.date()).first()

        if existing_entry:
                TemporaryAttendance.objects.filter(name=formatted_name,breakin__isnull=False,timeout__isnull=True, date=current_time.date()).update(timeout=formatted_time)
          

def breakout(name, current_time):
    formatted_time = current_time.strftime("%I:%M:%S")
    TemporaryAttendance.objects.filter(timein__isnull=False,breakout__isnull=True, name=name,date=current_time.date()).update(breakout=formatted_time)
    qr_existing = qr_existing_list.objects.filter(employee_unique_id=name).first()

    if qr_existing:
        formatted_name = f"{qr_existing.fn} {qr_existing.ln}"
        existing_entry = TemporaryAttendance.objects.filter(name=formatted_name, date=current_time.date()).first()

        if existing_entry:
                TemporaryAttendance.objects.filter(timein__isnull=False,breakout__isnull=True,name=formatted_name, date=current_time.date()).update(breakout=formatted_time)


def insertData(name, current_time, request):
    formatted_time = current_time.strftime("%I:%M:%S")
    branch_names = request.user.username

    qr_existing = qr_existing_list.objects.filter(employee_unique_id=name).first()
    
    if qr_existing is None:
     
        TemporaryAttendance.objects.filter(name=name, date=current_time.date()).create(
            name=name,
            timein=formatted_time,
            branch_name=branch_names,
        )
        Archive.objects.filter(name=name,date=current_time.date()).create(name=name,timein_names=name,timein_timestamps=current_time)
    else:
        formatted_name = f"{qr_existing.fn} {qr_existing.ln}"
        existing_entry = TemporaryAttendance.objects.filter(name=formatted_name, date=current_time.date()).first()

        if existing_entry is None:

            TemporaryAttendance.objects.filter(name=formatted_name, date=current_time.date()).create(
                name=formatted_name,
                timein=formatted_time,
                branch_name=branch_names,
            )
            Archive.objects.filter(name=name,date=current_time.date()).create(name=formatted_name,timein_names=formatted_name,timein_timestamps=current_time)




def breakin(name,current_time):
    formatted_time = current_time.strftime("%I:%M:%S")
    TemporaryAttendance.objects.filter(timein__isnull=False,breakout__isnull=False,breakin__isnull=True, name=name, date=current_time.date()).update(breakin=formatted_time)
    qr_existing = qr_existing_list.objects.filter(employee_unique_id=name).first()

    if qr_existing:
        formatted_name = f"{qr_existing.fn} {qr_existing.ln}"
        existing_entry = TemporaryAttendance.objects.filter(name=formatted_name, date=current_time.date()).first()

        if existing_entry:
                 TemporaryAttendance.objects.filter(name=formatted_name,timein__isnull=False,breakout__isnull=False,breakin__isnull=True, date=current_time.date()).update(breakin=formatted_time)


def timeout(name,current_time):
    formatted_time = current_time.strftime("%I:%M:%S")
    TemporaryAttendance.objects.filter(timein__isnull=False,breakin__isnull=False,breakout__isnull=False,timeout__isnull=True, name=name, date=current_time.date()).update(timeout=formatted_time)
    qr_existing = qr_existing_list.objects.filter(employee_unique_id=name).first()

    if qr_existing:
        formatted_name = f"{qr_existing.fn} {qr_existing.ln}"
        existing_entry = TemporaryAttendance.objects.filter(name=formatted_name, date=current_time.date()).first()

        if existing_entry:
            TemporaryAttendance.objects.filter(timein__isnull=False,breakin__isnull=False,breakout__isnull=False,timeout__isnull=True, name=formatted_name, date=current_time.date()).update(timeout=formatted_time)
    
    
def deleteTable():
        Archive.objects.exclude(date=date.today()).delete()
    
    
def qr_code_scanner(request):
    return render(request, 'temp_myapp/qr_scanner.html')


def display_qr_list(request):
    current_date = date.today()
    attendances = TemporaryAttendance.objects.filter(date=current_date).order_by('-breakout', '-breakin', '-timeout', '-timein')

    def custom_sort(attendance):
        times = [attendance.breakout, attendance.breakin, attendance.timeout]
        latest_time = max(filter(None, times), default=None)

        if latest_time is not None:
            latest_time = datetime.strptime(latest_time, '%H:%M:%S').time()

        return latest_time or datetime.min.time()

    sorted_attendances = sorted(attendances, key=custom_sort, reverse=True)

    data = [
        {
            'name': attendance.name,
            'timein': str(attendance.timein),
            'breakout': str(attendance.breakout),
            'breakin': str(attendance.breakin),
            'timeout': str(attendance.timeout)
        } for attendance in sorted_attendances
    ]

    return JsonResponse({'attendances': data})




