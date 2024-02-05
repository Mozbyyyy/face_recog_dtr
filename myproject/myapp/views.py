from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy
from django.views.generic import ListView
from .models import Student
from .models import TemporaryAttendance
from .models import Archive
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponseRedirect
import base64
import cv2
from django.http import StreamingHttpResponse
import face_recognition
import os
import dlib
import math
import numpy as np
from functools import lru_cache
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,date,time
from datetime import timedelta
import json
from .app_views.edit_timein import edit_timein
from django.core.cache import cache
from .middleware import CurrentTimeMiddleware
import logging
from django.db import connection
import time
from django.db import transaction
import threading
from django.db import IntegrityError
from django.db.models import Max
import re
from django.utils import timezone
from scipy.spatial import distance as dist
from django.contrib.messages import get_messages
from django.views.decorators.csrf import csrf_exempt


#sql_file_pattern = re.compile(r'export_\d{4}-\d{2}-\d{2} \(\d+\)\.sql')
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')


def is_admin(user):
    return user.groups.filter(name='admingroup').exists()


@login_required(login_url='login')
def home(request):
    user_in_admingroup = is_admin(request.user)
    return render(request, 'temp_myapp/home.html', {'user_in_admingroup': user_in_admingroup})



@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def addemployee(request):
    query = request.POST.get("searchquery", "")


    if query:
        student_list = Student.objects.filter(Q(firstname__icontains=query) | Q(lastname__icontains=query) | Q(code__icontains=query))
    else:
        student_list = Student.objects.all().order_by('id')

    page = request.GET.get('page', 1)
    paginator = Paginator(student_list, 10)  # Show 10 items per page

    try:
        student_list = paginator.page(page)
    except PageNotAnInteger:
        student_list = paginator.page(1)
    except EmptyPage:
        student_list = paginator.page(paginator.num_pages)


    if request.method == "POST":
        if "add" in request.POST:
            firstname = request.POST.get("firstname")
            middlename = request.POST.get("middlename")
            lastname = request.POST.get("lastname")
            branch = request.POST.get("branch")

            # Find the latest code, extract the numeric part, increment it, and create a new code
            latest_code = Student.objects.all().aggregate(Max('code'))['code__max']
            latest_numeric_part = int(re.search(r'\d+', latest_code).group()) if latest_code else 0
            new_code_numeric_part = latest_numeric_part + 1
            new_code = f"EMB{new_code_numeric_part:05d}"

            try:
                Student.objects.create(
                    code=new_code,
                    firstname=firstname,
                    middlename=middlename,
                    lastname=lastname,
                    branch=branch
                )
                messages.success(request, 'Data added successfully!', extra_tags='added')
            except IntegrityError:
                # Handle integrity error (e.g., if by some rare chance a conflict still occurs)
                messages.error(request, 'Error adding data. Please try again.', extra_tags='error')

            return HttpResponseRedirect(request.path)
            # return redirect('addemployee')

        elif "update" in request.POST:
            id = request.POST.get("id")
            firstname = request.POST.get("firstname")
            middlename = request.POST.get("middlename")
            lastname = request.POST.get("lastname")
            branch = request.POST.get("branch")

            update_student = Student.objects.get(id=id)
            update_student.firstname = firstname
            update_student.middlename = middlename
            update_student.lastname = lastname
            update_student.branch = branch
            update_student.save()
            messages.success(request, 'Data updated successfully!',extra_tags='updated')
            return HttpResponseRedirect(request.path)


        elif "delete" in request.POST:
            id = request.POST.get("id")
            Student.objects.get(id=id).delete()
            # Redirect after the form is successfully submitted
            return redirect('addemployee')



    elif "search" in request.POST:
            query = request.POST.get("searchquery", "")
            if query:
                student_list = Student.objects.filter(Q(firstname__icontains=query) | Q(lastname__icontains=query) | Q(code__icontains=query))
            else:
                student_list = Student.objects.all().order_by('id')

            paginator = Paginator(student_list, 10)  # Reset paginator
            page = request.GET.get('page', 1)

            try:
                student_list = paginator.page(page)
            except PageNotAnInteger:
                student_list = paginator.page(1)
            except EmptyPage:
                student_list = paginator.page(paginator.num_pages)

            return render(request, 'temp_myapp/addemployee.html', {'student_list': student_list, 'query': query})

    return render(request, 'temp_myapp/addemployee.html', {'student_list': student_list, 'query': query})



def user_profile(request, pk):
    student = get_object_or_404(Student, id=pk)
    return render(request, 'temp_myapp/employeeprofile.html', {'student': student})




def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                if request.user.username == 'emb_payroll':
                    return redirect('addemployee')
                else:
                    return redirect('home')
            
    else:
        form = AuthenticationForm()
    return render(request, 'temp_myapp/login.html', {'form': form})




def get_next_code(request):
    latest_code = Student.objects.order_by('-code').first()
    if latest_code:
        current_number = int(latest_code.code[3:]) + 1
    else:
        current_number = 1

    new_code = f"EMB{current_number:04d}"
    return JsonResponse({'code': new_code})

























SHAPE_PREDICTOR_PATH = "myapp/assets/pre-trained/shape_predictor_68_face_landmarks.dat"
KNOWN_FACES_DIR = "myapp/try"
KNOWN_FACES_DIR2 = "myapp/xtian"
KNOWN_FACES_ALL = "myapp/PreTry"
FRAME_WIDTH = 720
FRAME_HEIGHT = 420
THRESHOLD = 0.4
cache_exp = 600


recognize_face_cache = {}







def recognize_face(face_encoding, known_face_encoding, known_face_name,request):
    current_time = datetime.now()
    if tuple(face_encoding) in recognize_face_cache and current_time.timestamp() - recognize_face_cache[tuple(face_encoding)]["timestamp"] < cache_exp:
        return recognize_face_cache[tuple(face_encoding)]["name"]



    matches = face_recognition.compare_faces(known_face_encoding, face_encoding, tolerance=THRESHOLD)

    if True in matches:
        first_match_index = matches.index(True)
        name = known_face_name[first_match_index]

        prac_time = current_time.strftime("%H:%M")

        recognize_face_cache[tuple(face_encoding)] = {"name": name, "timestamp": current_time.timestamp()}



        if "06:00" <= prac_time <= "08:00":
            deleteTable()

        if "03:00" <= prac_time <= "10:59":

            existing_entry = TemporaryAttendance.objects.filter(name=name,date=current_time.date()).first()
            if existing_entry is None:
                insertData(name, current_time,request)
                Archive.objects.filter(name=name,date=current_time.date()).create(name=name,timein_names=name,timein_timestamps=current_time)
                return "Successfully timein..."
           
               



        if "12:00" <= prac_time <= "13:00" and Archive.objects.filter(name=name, timein_names__isnull=False, breakout_names__isnull=True, date=current_time.date()).exists():
            existing_entry = Archive.objects.filter(name=name, date=current_time.date()).first()

            existing_entry_timein_timestamps = existing_entry.timein_timestamps.replace(tzinfo=timezone.utc)
            current_time = current_time.replace(tzinfo=timezone.utc)

            time_difference = current_time - existing_entry_timein_timestamps
            remaining_seconds = max(15 - time_difference.total_seconds(), 0)

            if current_time - existing_entry_timein_timestamps >= timedelta(seconds=15):
                breakout(name, current_time)
                Archive.objects.filter(name=name, date=current_time.date()).update(breakout_names=name,breakout_timestamps=current_time)
            #     return "Successfully Breakout..."
            # else:
            #     return f"please wait...{int(remaining_seconds)} seconds"


        if "12:00" <= prac_time <= "14:00" and Archive.objects.filter(name=name, timein_names__isnull=False, breakout_names__isnull=False,breakin_names__isnull=True, date=current_time.date()).exists():
            existing_entry2 = Archive.objects.filter(name=name, date=current_time.date()).first()

            existing_entry_breakout_timestamps = existing_entry2.breakout_timestamps.replace(tzinfo=timezone.utc)
            current_time = current_time.replace(tzinfo=timezone.utc)

            time_difference = current_time - existing_entry_breakout_timestamps
            remaining_seconds = max(15 - time_difference.total_seconds(), 0)

            if current_time - existing_entry_breakout_timestamps >= timedelta(seconds=15):
                breakin(name, current_time)
                Archive.objects.filter(name=name, date=current_time.date()).update(breakin_names=name,breakin_timestamps=current_time)
            #     return "Successfully Breakin..."
            # else:
            #     return f"please wait...{int(remaining_seconds)} seconds"

        if "15:00" <= prac_time <= "23:59" and Archive.objects.filter(name=name, timein_names__isnull=False, breakout_names__isnull=False,breakin_names__isnull=False, timeout_names__isnull=True,date=current_time.date()).exists():
            existing_entry3 = Archive.objects.filter(name=name, date=current_time.date()).first()

            existing_entry_breakin_timestamps = existing_entry3.breakin_timestamps.replace(tzinfo=timezone.utc)
            current_time = current_time.replace(tzinfo=timezone.utc)

            time_difference = current_time - existing_entry_breakin_timestamps
            remaining_seconds = max(30 - time_difference.total_seconds(), 0)

            if current_time - existing_entry_breakin_timestamps >= timedelta(seconds=30):
                timeout(name, current_time)
                Archive.objects.filter(name=name, date=current_time.date()).update(breakin_names=name,timeout_timestamps=current_time)
            #     return "Successfully Timeout..."
            # else:
            #     return f"please wait...{int(remaining_seconds)} seconds"



        if "15:00" <= prac_time <= "23:59" and Archive.objects.filter(name=name, timein_names__isnull=False, breakin_names__isnull=True,breakout_names__isnull=True, date=current_time.date()).exists():
            return "NO BREAKOUT OR BREAKIN"
            


    #if login afternoon

        if "11:00" <= prac_time <= "23:59":
            existing_entry = TemporaryAttendance.objects.filter(name=name,date=current_time.date()).first()
            if existing_entry is None:
                afternoonBreakout(name, current_time,request)
                Archive.objects.filter(name=name,date=current_time.date()).create(name=name,breakin_names=name,breakin_timestamps=current_time)

            if "15:00" <= prac_time <= "23:59" and Archive.objects.filter(name=name, breakin_names__isnull=False, timeout_names__isnull=True, date=current_time.date()).exists():
                existing_entry = Archive.objects.filter(name=name, date=current_time.date()).first()

                existing_entry_breakin_timestamps = existing_entry.breakin_timestamps.replace(tzinfo=timezone.utc)
                current_time = current_time.replace(tzinfo=timezone.utc)

                time_difference = current_time - existing_entry_breakin_timestamps
                remaining_seconds = max(15 - time_difference.total_seconds(), 0)

                if current_time - existing_entry_breakin_timestamps >= timedelta(seconds=15):
                    afternoonTimeout(name, current_time)
                    Archive.objects.filter(name=name, date=current_time.date()).update(timeout_names=name,timeout_timestamps=current_time)
                #     return "Successfully Breakout..."
                # else:
                #     return f"please wait...{int(remaining_seconds)} seconds"
                
                
        return name


    
        

    return "Analyzing.."





        
    



def afternoonBreakout(name,current_time,request):
    formatted_time = current_time.strftime("%I:%M:%S")
    branch_names = request.user.username
    TemporaryAttendance.objects.filter(name=name,date=current_time.date()).create(name=name,breakin=formatted_time,branch_name=branch_names)

def afternoonTimeout(name,current_time):
    formatted_time = current_time.strftime("%I:%M:%S")
    TemporaryAttendance.objects.filter(name=name,breakin__isnull=False,date=current_time.date()).update(timeout=formatted_time)

def breakout(name, current_time):
    formatted_time = current_time.strftime("%I:%M:%S")
    TemporaryAttendance.objects.filter(timein__isnull=False,breakout__isnull=True, name=name,date=current_time.date()).update(breakout=formatted_time)


def insertData(name,current_time,request):
    formatted_time = current_time.strftime("%I:%M:%S")
    branch_names = request.user.username
    TemporaryAttendance.objects.filter(name=name,date=current_time.date()).create(name=name,timein=formatted_time,branch_name=branch_names)

def breakin(name,current_time):
    formatted_time = current_time.strftime("%I:%M:%S")
    TemporaryAttendance.objects.filter(timein__isnull=False,breakout__isnull=False,breakin__isnull=True, name=name, date=current_time.date()).update(breakin=formatted_time)

def timeout(name,current_time):
    formatted_time = current_time.strftime("%I:%M:%S")
    TemporaryAttendance.objects.filter(timein__isnull=False,breakin__isnull=False,breakout__isnull=False,timeout__isnull=True, name=name, date=current_time.date()).update(timeout=formatted_time)



def deleteTable():
        Archive.objects.exclude(date=date.today()).delete()



def preprocess(frame):
    face_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return face_gray

def apply_lighting_augmentation(image, alpha, beta):
    augmented_image = cv2.addWeighted(image, alpha, np.zeros(image.shape, image.dtype), 0, beta)
    augmented_image = np.clip(augmented_image, 0, 255)
    return augmented_image

def load_known_faces(request):
    known_face_encodings = []
    known_face_names = []
    
    # if request.user.username == 'admin':
    #     x = KNOWN_FACES_DIR
    # elif request.user.username == 'emb_main':
    #     x = KNOWN_FACES_DIR2
    # elif request.user.username == 'user':
    #     x = KNOWN_FACES_ALL


    for person_dir in os.listdir(KNOWN_FACES_DIR):
        person_path = os.path.join(KNOWN_FACES_DIR, person_dir)

        if os.path.isdir(person_path):
            person_name = person_dir  # Use the directory name as the person's name

            for filename in os.listdir(person_path):
                if filename.endswith(".jpg"):
                    image_path = os.path.join(person_path, filename)
                    person_image = face_recognition.load_image_file(image_path)

                    face_encodings = face_recognition.face_encodings(person_image)
                    if face_encodings:
                        person_encoding = face_encodings[0]
                        known_face_encodings.append(person_encoding)
                        known_face_names.append(person_name)

    return known_face_encodings, known_face_names



def calculate_eye_distance(left_eye, right_eye):
    delta_x = right_eye[0] - left_eye[0]
    delta_y = right_eye[1] - left_eye[1]
    angle = math.degrees(math.atan2(delta_y, delta_x))
    return angle






def gen_frames(request):
    known_face_encodings, known_face_names = load_known_faces(request)
    cap = cv2.VideoCapture(0)  # Open webcam
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)

    frame_skip = 6
    frame_count = 0

    while True:

        success, frame = cap.read()  # Read a frame from the webcam
        if not success:
            break

        if not success or frame is None:
            continue

        frame_count+=1

        if frame_count % frame_skip != 0:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        for face in faces:
            try:

                #calculate the shape of the bounding box to limit the classification
                min_width = 40
                min_height = 40

                if face.width() < min_width or face.height() < min_height:
                    return
                #calculate the shape of the bounding box to limit the classification


                landmarks = predictor(gray, face)
                left_eye = (landmarks.part(36).x, landmarks.part(36).y)
                right_eye = (landmarks.part(45).x, landmarks.part(45).y)

                # Calculate the rotation angle for orientation normalization
                angle = calculate_eye_distance(left_eye, right_eye)

                reference_distance = np.linalg.norm(np.array(left_eye) - np.array(right_eye))
                distance_between_eyes = np.sqrt((right_eye[0] - left_eye[0]) ** 2 + (right_eye[1] - left_eye[1]) ** 2)
                scale_factor = distance_between_eyes / reference_distance

                rotation_matrix = cv2.getRotationMatrix2D(left_eye, angle, scale_factor)

                aligned_face = cv2.warpAffine(frame, rotation_matrix, (frame.shape[1], frame.shape[0]))

                x, y, w, h = face.left(), face.top(), face.width(), face.height()
                aligned_face = aligned_face[y:y + h, x:x + w]

                new_width = 200
                new_height = 155

                aligned_face_rgb = preprocess(aligned_face)
                aligned_face_rgb = cv2.resize(aligned_face_rgb, (new_width, new_height))
                # Apply lighting augmentation
                augmented_face = apply_lighting_augmentation(aligned_face_rgb, alpha=1.2, beta=30)

                face_locations = face_recognition.face_locations(augmented_face)
                face_encodings = face_recognition.face_encodings(augmented_face, face_locations)



                #current_time = request.current_time
                current_time = datetime.now()



                with ThreadPoolExecutor() as executor:
                    futures = [executor.submit(recognize_face, face_encoding, known_face_encodings, known_face_names,request)
                            for face_encoding in face_encodings]

                    for future, (top, right, bottom, left) in zip(futures, face_locations):
                        name = future.result()

                     


                        cv2.rectangle(frame, (left + x, top + y), (right + x, bottom + y), (2, 195, 154), 2)

                        # Get the size of the text
                        text_size, _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_DUPLEX, 0.5, 1)

                        # Adjust the width of the filled rectangle based on the text size
                        rect_width = text_size[0] + 20  # Add some padding

                        # Adjust the position of the text and filled rectangle
                        text_position = (left + x - 5, bottom + y + 15)
                        rect_position = (left + x - 10, bottom + y)

                        cv2.rectangle(frame, rect_position, (rect_position[0] + rect_width, rect_position[1] + 23), (255, 0, 0),
                                    thickness=cv2.FILLED)
                        font = cv2.FONT_HERSHEY_DUPLEX
                        cv2.putText(frame, name, text_position, font, 0.5, (255, 255, 255), 1)


            except Exception as e:
                # Handle any exceptions that may occur during face processing
                print(f"An error occurred in gen_frames - : {str(e)}")

        ret, buffer = cv2.imencode('.jpg', frame)  # Encode the frame
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')




def camera_feed(request):
    return StreamingHttpResponse(gen_frames(request), content_type='multipart/x-mixed-replace; boundary=frame')






@login_required(login_url='login')
def facedetection(request):
    attendances = TemporaryAttendance.objects.all().order_by('id')
    return render(request, 'temp_myapp/facedetection.html',{'attendances':attendances})




def get_attendance_data(request):
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
