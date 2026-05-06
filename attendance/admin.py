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
        'employee',
        'date',
        'time_in',
        'time_out',
        'worked_hours',
        'payable_hours',
        'late_minutes',
        'undertime_minutes',
        'transportation_fee_applicable',
        'remarks',
    )

    list_filter = (
        'date',
        'employee',
        'transportation_fee_applicable',
    )

    search_fields = (
        'employee__employee_id',
        'employee__first_name',
        'employee__last_name',
        'remarks',
    )

    readonly_fields = (
        'worked_hours',
        'payable_hours',
        'late_minutes',
        'undertime_minutes',
    )

    def bulk_entry_link(self, request):
        url = reverse('admin:attendance-bulk-entry')
        return format_html(
            '<a class="button" href="{}" style="padding:8px 12px; background:#417690; color:white; border-radius:4px; text-decoration:none;">Bulk Attendance Entry</a>',
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
                date = form.cleaned_data['date']
                time_in = form.cleaned_data['time_in']
                time_out = form.cleaned_data['time_out']
                employees = form.cleaned_data['employees']
                transportation_fee_applicable = form.cleaned_data['transportation_fee_applicable']

                created_count = 0
                updated_count = 0

                for employee in employees:
                    time_in_datetime = timezone.make_aware(
                        datetime.combine(date, time_in)
                    )
                    time_out_datetime = timezone.make_aware(
                        datetime.combine(date, time_out)
                    )

                    attendance, created = Attendance.objects.update_or_create(
                        employee=employee,
                        date=date,
                        defaults={
                            'time_in': time_in_datetime,
                            'time_out': time_out_datetime,
                            'transportation_fee_applicable': transportation_fee_applicable,
                        }
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
            context
        )