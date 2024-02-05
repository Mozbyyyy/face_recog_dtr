from django.shortcuts import render,redirect
from django.http import HttpResponse
from myapp.forms import DateSelectionForm
from myapp.models import TemporaryAttendance
from cryptography.fernet import Fernet
import requests
import os
import tempfile
from django.contrib import messages
from django.http import Http404


def encrypt_content(content, password):
    cipher_suite = Fernet(password)
    encrypted_content = cipher_suite.encrypt(content.encode())
    return encrypted_content

def export_data(request):
    if request.method == 'POST':
        form = DateSelectionForm(request.POST)
        if form.is_valid():
            selected_date = form.cleaned_data['selected_date']
            username = request.user.username

            # Check if there are files for the selected date
            data = TemporaryAttendance.objects.filter(date=selected_date)
            if not data.exists():
                return HttpResponse(f"No data found for the selected date: {selected_date}", status=404)

            sql_content = "\n".join([obj.to_sql() for obj in data])

            encryption_password = b'-qSaMATH3hnZqbD-DHPkQD9lXsxU59OOZZr7rfgSNbw='  # Replace with your password
            encrypted_sql_content = encrypt_content(sql_content, encryption_password)

            # Create a temporary file in the user's download directory
            temp_file_path = os.path.join(os.path.expanduser('~'), 'Downloads', f'export_{selected_date}_{username}.encrypted')
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(encrypted_sql_content)

            # Read the content once and use it for both HttpResponse and requests.post
            with open(temp_file_path, 'rb') as file:
                file_content = file.read()

            # Download the encrypted file
            response = HttpResponse(file_content, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename=export_{selected_date}_{username}.encrypted'

            # Send the file to the specified endpoint with a custom filename
            file_data = {'file': (f'export_{selected_date}_{username}.encrypted', file_content)}
            upload_url = 'https://jgcintegratedsystems.com/views/modules/autoupload.php'
            response_upload = requests.post(upload_url, files=file_data)

            if response_upload.status_code == 200:
                messages.success(request, 'Data exported successfully!', extra_tags='export')
                return redirect(request.path)
            else:
                return HttpResponse("Failed to upload the file to the external endpoint. Check the server response.")
    else:
        form = DateSelectionForm()

    return render(request, 'temp_myapp/exportDTR.html', {'form': form})



def export_data_afternoon(request):
    if request.method == 'POST':
        form = DateSelectionForm(request.POST)
        if form.is_valid():
            selected_date = form.cleaned_data['selected_date']
            username = request.user.username

            data = TemporaryAttendance.objects.filter(date=selected_date)
            if not data.exists():
                return HttpResponse(f"No data found for the selected date: {selected_date}", status=404)
                
            sql_content = "\n".join([obj.to_sql_all() for obj in data])

            encryption_password = b'-qSaMATH3hnZqbD-DHPkQD9lXsxU59OOZZr7rfgSNbw='  # Replace with your password
            encrypted_sql_content = encrypt_content(sql_content, encryption_password)

            # Create a temporary file in the user's download directory
            temp_file_path = os.path.join(os.path.expanduser('~'), 'Downloads', f'export_{selected_date}_{username}.encrypted')
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(encrypted_sql_content)

            # Read the content once and use it for both HttpResponse and requests.post
            with open(temp_file_path, 'rb') as file:
                file_content = file.read()

            # Download the encrypted file
            response = HttpResponse(file_content, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename=export_{selected_date}_{username}.encrypted'

            # Send the file to the specified endpoint with a custom filename
            file_data = {'file': (f'export_{selected_date}_{username}.encrypted', file_content)}
            upload_url = 'https://jgcintegratedsystems.com/views/modules/autoupload.php'
            response_upload = requests.post(upload_url, files=file_data)

            if response_upload.status_code == 200:
                messages.success(request, 'Data exported successfully!', extra_tags='export')
                return redirect(request.path)
            else:
                return HttpResponse("Failed to upload the file to the external endpoint. Check the server response.")
    else:
        form = DateSelectionForm()

    return render(request, 'temp_myapp/exportDTR.html', {'form': form})














# from django.shortcuts import render
# from django.shortcuts import render
# from django.http import HttpResponse
# from myapp.forms import DateSelectionForm
# from myapp.models import TemporaryAttendance

# def export_data(request):
#     if request.method == 'POST':
#         form = DateSelectionForm(request.POST)
#         if form.is_valid():
#             selected_date = form.cleaned_data['selected_date']

#             data = TemporaryAttendance.objects.filter(date=selected_date)


#             sql_content = "\n".join([obj.to_sql() for obj in data])


#             response = HttpResponse(sql_content, content_type='application/sql')
#             response['Content-Disposition'] = f'attachment; filename=export_{selected_date}.sql'
#             return response
#     else:
#         form = DateSelectionForm()

#     return render(request, 'temp_myapp/exportDTR.html', {'form': form})
