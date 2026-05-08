from datetime import datetime

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Attendance
from .forms import AttendanceAdminForm
from .forms_bulk import AttendanceBulkEntryForm


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    form = AttendanceAdminForm

    list_display = (
        'employee_id',
        'employee_name',
        'date',
        'status',
        'time_in',
        'time_out',
        'worked_hours',
        'payable_hours',
        'late_minutes',
        'undertime_minutes',
        'overtime_applicable',
        'overtime_minutes',
        'transportation_fee_applicable',
        'work_type',
        'delivery_allowance_applicable',
        'work_location',
        'remarks',
    )

    list_filter = (
        'date',
        'status',
        'employee',
        'overtime_applicable',
        'transportation_fee_applicable',
        'work_type',
        'delivery_allowance_applicable',
    )

    date_hierarchy = 'date'

    ordering = (
        '-date',
        'employee__employee_id',
    )

    list_per_page = 50

    search_fields = (
        'employee__employee_id',
        'employee__first_name',
        'employee__last_name',
        'work_location',
        'remarks',
    )

    readonly_fields = (
        'worked_hours',
        'payable_hours',
        'late_minutes',
        'undertime_minutes',
        'overtime_minutes',
    )

    def employee_id(self, obj):
        return obj.employee.employee_id
    employee_id.short_description = 'Employee ID'
    employee_id.admin_order_field = 'employee__employee_id'

    def employee_name(self, obj):
        return obj.employee.full_name
    employee_name.short_description = 'Employee Name'
    employee_name.admin_order_field = 'employee__last_name'

    def bulk_entry_link(self, request):
        url = reverse('admin:attendance-bulk-entry')
        return format_html(
            '<a class="button" href="{}" '
            'style="padding:8px 12px; background:#417690; color:white; '
            'border-radius:4px; text-decoration:none;">'
            'Bulk Attendance Entry</a>',
            url
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['bulk_entry_link'] = self.bulk_entry_link(request)
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'bulk-entry/',
                self.admin_site.admin_view(self.bulk_entry_view),
                name='attendance-bulk-entry',
            ),
        ]
        return custom_urls + urls

    def bulk_entry_view(self, request):
        if request.method == 'POST':
            form = AttendanceBulkEntryForm(request.POST)

            if form.is_valid():
                date = form.cleaned_data.get('date')
                employees = form.cleaned_data.get('employees')

                status = form.cleaned_data.get('status') or 'present'
                time_in = form.cleaned_data.get('time_in')
                time_out = form.cleaned_data.get('time_out')

                overtime_applicable = form.cleaned_data.get(
                    'overtime_applicable',
                    False
                )

                transportation_fee_applicable = form.cleaned_data.get(
                    'transportation_fee_applicable',
                    False
                )

                work_type = form.cleaned_data.get('work_type', 'office')

                delivery_allowance_applicable = form.cleaned_data.get(
                    'delivery_allowance_applicable',
                    False
                )

                work_location = form.cleaned_data.get('work_location', '')
                remarks = form.cleaned_data.get('remarks', '')

                if not date:
                    messages.error(request, 'Please select a date.')
                    return redirect('admin:attendance-bulk-entry')

                if not employees:
                    messages.error(request, 'Please select at least one employee.')
                    return redirect('admin:attendance-bulk-entry')

                if work_type != 'deliver':
                    delivery_allowance_applicable = False

                created_count = 0
                updated_count = 0

                no_time_statuses = ['absent', 'leave', 'rest_day', 'holiday']

                for employee in employees:
                    defaults = {
                        'status': status,
                        'overtime_applicable': overtime_applicable,
                        'transportation_fee_applicable': transportation_fee_applicable,
                        'work_type': work_type,
                        'delivery_allowance_applicable': delivery_allowance_applicable,
                        'work_location': work_location,
                        'remarks': remarks,
                    }

                    if status in no_time_statuses:
                        defaults['time_in'] = None
                        defaults['time_out'] = None
                        defaults['overtime_applicable'] = False
                        defaults['transportation_fee_applicable'] = False
                        defaults['delivery_allowance_applicable'] = False
                    else:
                        defaults['time_in'] = (
                            timezone.make_aware(datetime.combine(date, time_in))
                            if time_in else None
                        )

                        defaults['time_out'] = (
                            timezone.make_aware(datetime.combine(date, time_out))
                            if time_out else None
                        )

                    attendance, created = Attendance.objects.update_or_create(
                        employee=employee,
                        date=date,
                        defaults=defaults,
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                messages.success(
                    request,
                    f'Bulk attendance saved. Created: {created_count}, Updated: {updated_count}.'
                )

                return redirect('admin:attendance_attendance_changelist')

            messages.error(request, 'Please correct the errors below.')

        else:
            form = AttendanceBulkEntryForm()

        context = dict(
            self.admin_site.each_context(request),
            title='Bulk Attendance Entry',
            form=form,
        )

        return TemplateResponse(
            request,
            'admin/attendance/attendance/bulk_entry.html',
            context,
        )