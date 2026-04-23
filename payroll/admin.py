from django.contrib import admin
from .models import Payroll


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'start_date',
        'end_date',
        'total_payable_hours',
        'total_salary',
        'created_at',
    )

    search_fields = (
        'employee__employee_id',
        'employee__first_name',
        'employee__last_name',
    )

    list_filter = (
        'start_date',
        'end_date',
        'employee',
    )

    readonly_fields = (
        'total_payable_hours',
        'total_salary',
        'created_at',
    )