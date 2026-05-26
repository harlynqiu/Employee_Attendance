from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('attendance-page/', views.attendance_page_view, name='attendance_page'),
    path('employees-page/', views.employees_page_view, name='employees_page'),
    path('new-employee/', views.new_employee_page_view, name='new_employee_page'),
    path('employees-page/<int:employee_id>/', views.view_employee_page_view, name='view_employee_page'),
    path('employees-page/edit/<int:employee_id>/', views.edit_employee_page_view, name='edit_employee_page'),
    path("charges/", views.charges_page_view, name="charges-page"),
]