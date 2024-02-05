import os
import re
from django.db import connection
from django.shortcuts import render,redirect
from django.http import HttpResponse
from myapp.forms import ImportForm
from myapp.models import TemporaryAttendance
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponseRedirect
from cryptography.fernet import Fernet
import json
from django.core.cache import cache
import requests



def decrypt_content(encrypted_content, password):
    cipher_suite = Fernet(password)
    decrypted_content = cipher_suite.decrypt(encrypted_content)
    return decrypted_content.decode()




def import_data(request):
    if request.method == 'POST':
        form = ImportForm(request.POST)
        if form.is_valid():
            selected_date = form.cleaned_data['date']

            # Try different variations of the filename until a valid one is found
            possible_variations = ['admin', 'embiloilo', 'emb-danao']

            for variation in possible_variations:
                php_website_url = f'https://jgcintegratedsystems.com/views/files/branchdtr/export_{selected_date}_{variation}.encrypted'

                try:
                    response = requests.get(php_website_url)
                    response.raise_for_status()
                    encrypted_sql_content = response.content  # Use response.content to get binary content
                    break  # Break out of the loop if a valid variation is found
                except requests.exceptions.RequestException:
                    pass  # Try the next variation if the current one is not found

            else:
                # If none of the variations are found, display an error message
                messages.error(request, f'Error fetching encrypted SQL file: File not found for selected date', extra_tags='ErrorAlert')
                return HttpResponseRedirect(request.path)

            # Decrypt the content using your decryption function
            decryption_key = b'-qSaMATH3hnZqbD-DHPkQD9lXsxU59OOZZr7rfgSNbw='
            decrypted_sql_content = decrypt_content(encrypted_sql_content, decryption_key)

            # Execute the decrypted SQL content using Django's connection
            with connection.cursor() as cursor:
                print(decrypted_sql_content)
                cursor.execute(decrypted_sql_content)

            messages.success(request, 'Data import successfully!', extra_tags='importAll')
            return HttpResponseRedirect(request.path)

    else:
        form = ImportForm()

    return render(request, 'temp_myapp/import_data.html', {'form': form})









def import_single_file_function(uploaded_file):
    encrypted_sql_content = uploaded_file.read()
    decryption_key = b'-qSaMATH3hnZqbD-DHPkQD9lXsxU59OOZZr7rfgSNbw='

    try:
        if encrypted_sql_content.strip():
            # Decrypt the content using the provided key
            decrypted_sql_content = decrypt_content(encrypted_sql_content, decryption_key)

            with connection.cursor() as cursor:
                cursor.execute(decrypted_sql_content)
        else:
            print("Error: Empty SQL file")
            return False

    except Exception as e:
        print(f"Error importing file: {e}")
        return False

    return True


def import_single_file(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')

        if uploaded_file:
            import_result = import_single_file_function(uploaded_file)

            if import_result:
                messages.success(request, 'Data import successfully!', extra_tags='singleImport')
                return redirect('import_data')
            else:
                messages.error(request, 'Error importing file', extra_tags='singleImportError')
        else:
            messages.error(request, 'No file uploaded', extra_tags='singleImportError')

    # Render the HTML even if the request method is not POST
    return render(request, 'temp_myapp/import_data.html')




def display_import_list(request):
    attendances = TemporaryAttendance.objects.values('name', 'branch_name', 'date').order_by('-date','-id')

    data = [
        {
            'name': attendance['name'],
            'branch_name': attendance['branch_name'],
            'date': attendance['date'],
        }
        for attendance in attendances
    ]

    return JsonResponse({'attendances': data})
