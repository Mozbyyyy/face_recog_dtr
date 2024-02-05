from django.urls import path
from myapp.views import login_view
from myapp import views
from .payroll_views.payroll_home import payroll_home

urlpatterns = [ 
	path('', views.login_view, name='login'),
	path('home_payroll/',payroll_home, name='payroll_home'),
  	path('logout/', views.CustomLogoutView.as_view(), name='logout'),
]

