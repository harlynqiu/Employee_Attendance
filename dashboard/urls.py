from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('attendance-page/', views.attendance_page_view, name='attendance_page'),
]