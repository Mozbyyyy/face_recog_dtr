# from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from .app_views.edit_timein import edit_timein
from django.contrib.auth import views as auth_views
from .views import get_next_code
from django.views.generic.base import TemplateView
from .app_views.export_data import export_data,export_data_afternoon
from .app_views.qr_generator import generate_qr_code
from .app_views.import_data import import_data,display_import_list,import_single_file
from django.conf.urls.static import static
from django.conf import settings
from .app_views.qr_scanner import qr_code_scanner,webcam_qr_code_scanner,display_qr_list,fetch_messages
from .app_views.dbf_to_sql import dbf_to_sql
from .app_views.print_page import print_page





urlpatterns = [
     path('', views.login_view, name='login'),
     path('home/', views.home, name='home'),
     path('logout/', views.CustomLogoutView.as_view(), name='logout'),
     path('addemployee/', views.addemployee, name="addemployee"),
     path('get_next_code/', get_next_code, name='get_next_code'),
     path('facedetection/',views.facedetection, name='facedetection'),
     path('camera_feed/', views.camera_feed, name='camera_feed'),
     path('get_attendance_data/', views.get_attendance_data, name='get_attendance_data'),
     path('user_profile/<int:pk>/', views.user_profile, name='user_profile'),
     path('editTimein/', edit_timein, name="edit_timein"),
     path('export/', export_data, name='export_data'),
     path('import/', import_data, name='import_data'),
     path('importlist/', display_import_list, name='display_import_list'),
     path('singleimport/', import_single_file, name='import_single_file'),
     path('QR_list/', generate_qr_code, name='generate_qr_code'),
     path('qr_code_scanner/', qr_code_scanner, name='qr_code_scanner'),
     path('webcam_qr_code_scanner/', webcam_qr_code_scanner, name='webcam_qr_code_scanner'),
     path('display_qr_list/', display_qr_list, name='display_qr_list'),
     path('dbf_to_sql/', dbf_to_sql, name='dbf_to_sql'),
     path('fetch_messages/', fetch_messages, name='fetch_messages'),
     path('print/', print_page, name='print_page'),
     path('export_all/', export_data_afternoon, name='export_data_afternoon'),
] 



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
