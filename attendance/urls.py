from django.urls import path
from .views import time_in_view, time_out_view, attendance_list_view

urlpatterns = [
    path('time-in/', time_in_view, name='time-in'),
    path('time-out/', time_out_view, name='time-out'),
    path('', attendance_list_view, name='attendance-list'),
]