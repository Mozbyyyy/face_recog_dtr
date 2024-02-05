from django.shortcuts import render

def edit_timein(request):
    return render(request, 'temp_myapp/timeinEdit.html')

