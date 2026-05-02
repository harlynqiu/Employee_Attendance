from django.contrib import admin
from .models import Attendance
from .forms import AttendanceAdminForm


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    form = AttendanceAdminForm

    list_display = (
        'employee',
        'date',
        'time_in',
        'time_out',
        'worked_hours',
        'payable_hours',
        'late_minutes',
        'undertime_minutes',
    )

    list_filter = (
        'date',
        'employee',
    )

    search_fields = (
        'employee__employee_id',
        'employee__first_name',
        'employee__last_name',
    )

    readonly_fields = (
        'worked_hours',
        'payable_hours',
        'late_minutes',
        'undertime_minutes',
    )