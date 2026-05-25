from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EmployeeViewSet,
    employees_page,
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)

urlpatterns = [

    # API
    path('', include(router.urls)),

    # EMPLOYEE PAGE
    path(
        'employees-page/',
        employees_page,
        name='employees-page'
    ),
]