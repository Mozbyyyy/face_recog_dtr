from django.shortcuts import render






def print_page(request):
	return render(request, 'temp_myapp/print_page.html')