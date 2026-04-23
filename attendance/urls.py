from django.urls import path
from .views import (
    time_in_view,
    time_out_view,
    attendance_list_view,
    employee_attendance_view,
    employee_weekly_attendance_view,
    employee_monthly_attendance_view,
    employee_attendance_by_month_view,
    employee_attendance_by_range_view,
    employee_summary_by_month_view,
    employee_summary_by_range_view,
)

urlpatterns = [
    path('time-in/', time_in_view, name='time-in'),
    path('time-out/', time_out_view, name='time-out'),
    path('', attendance_list_view, name='attendance-list'),

    path('employee/<str:employee_id>/', employee_attendance_view, name='employee-attendance'),
    path('employee/<str:employee_id>/weekly/', employee_weekly_attendance_view, name='employee-weekly-attendance'),
    path('employee/<str:employee_id>/monthly/', employee_monthly_attendance_view, name='employee-monthly-attendance'),

    path('employee/<str:employee_id>/by-month/', employee_attendance_by_month_view, name='employee-attendance-by-month'),
    path('employee/<str:employee_id>/by-range/', employee_attendance_by_range_view, name='employee-attendance-by-range'),

    path('employee/<str:employee_id>/summary/by-month/', employee_summary_by_month_view, name='employee-summary-by-month'),
    path('employee/<str:employee_id>/summary/by-range/', employee_summary_by_range_view, name='employee-summary-by-range'),
]