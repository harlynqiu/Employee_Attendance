"""
URL configuration for EmployeeAttendance project.
"""

from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    # API ROUTES
    path('api/', include('employees.urls')),
    path('api/attendance/', include('attendance.urls')),

    # DASHBOARD ROUTES
    path('', include('dashboard.urls')),
]


# ==============================
# MEDIA FILES
# For uploaded employee photos,
# government documents, QR codes
# ==============================

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )