from django.urls import path
from . import views

urlpatterns = [
    path("", views.payroll_page, name="payroll-page"),
    path("add/", views.add_payroll, name="add-payroll"),
    path("view/<int:payroll_id>/", views.view_payroll, name="view-payroll"),
    path("edit/<int:payroll_id>/", views.edit_payroll, name="edit-payroll"),
]