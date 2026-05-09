from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'last_name', 'first_name', 'position', 'salary_type', 'rate')
    readonly_fields = ('employee_id',)
    search_fields = ('first_name', 'last_name', 'employee_id')