"""
URL configuration for EmployeeAttendance project.
"""

from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from payroll.views import (
    payroll_page,
    add_payroll,
)

from employees.views import (
    employees_page,
)


urlpatterns = [

    # =========================
    # DJANGO ADMIN
    # =========================
    path(
        'admin/',
        admin.site.urls
    ),

    # =========================
    # EMPLOYEE PAGE
    # =========================
    path(
        'employees-page/',
        employees_page,
        name='employees-page'
    ),

    # =========================
    # CUSTOM PAYROLL PAGES
    # =========================
    path(
        'payroll-page/',
        payroll_page,
        name='payroll-page'
    ),

    path(
        'payroll-page/add/',
        add_payroll,
        name='add-payroll'
    ),

    # =========================
    # API ROUTES
    # =========================
    path(
        'api/',
        include('employees.urls')
    ),

    path(
        'api/attendance/',
        include('attendance.urls')
    ),

    # =========================
    # DASHBOARD ROUTES
    # =========================
    path(
        '',
        include('dashboard.urls')
    ),
]


# =========================
# MEDIA FILES
# =========================

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )