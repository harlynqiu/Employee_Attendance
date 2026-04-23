from django.contrib import admin
from django.db.models import Sum
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Attendance
from .forms import AttendanceAdminForm
from .forms_summary import AttendanceSummaryForm


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

    list_filter = ('date', 'employee')

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

    def summary_link(self, request):
        url = reverse('admin:attendance-attendance-summary')
        return format_html(
            '<a class="button" href="{}" style="padding:8px 12px; background:#417690; color:white; border-radius:4px; text-decoration:none;">View Attendance Summary</a>',
            url
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['summary_link'] = self.summary_link(request)

        response = super().changelist_view(request, extra_context)

        try:
            queryset = response.context_data['cl'].queryset
            summary = queryset.aggregate(
                total_payable_hours=Sum('payable_hours'),
                total_late_minutes=Sum('late_minutes'),
                total_undertime_minutes=Sum('undertime_minutes'),
            )

            response.context_data['summary'] = {
                'total_payable_hours': summary['total_payable_hours'] or 0,
                'total_late_minutes': summary['total_late_minutes'] or 0,
                'total_undertime_minutes': summary['total_undertime_minutes'] or 0,
            }
        except (AttributeError, KeyError, TypeError):
            pass

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'summary/',
                self.admin_site.admin_view(self.summary_view),
                name='attendance-attendance-summary',
            ),
        ]
        return custom_urls + urls

    def summary_view(self, request):
        form = AttendanceSummaryForm(request.GET or None)
        attendance = Attendance.objects.select_related('employee').all().order_by(
            'employee__last_name',
            'employee__first_name',
            'date'
        )

        if form.is_valid():
            employee = form.cleaned_data.get('employee')
            year = form.cleaned_data.get('year')
            month = form.cleaned_data.get('month')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            if employee:
                attendance = attendance.filter(employee=employee)

            if year and month:
                attendance = attendance.filter(date__year=year, date__month=month)

            if start_date and end_date:
                attendance = attendance.filter(date__range=[start_date, end_date])
            elif start_date:
                attendance = attendance.filter(date__gte=start_date)
            elif end_date:
                attendance = attendance.filter(date__lte=end_date)

        totals = attendance.aggregate(
            total_payable_hours=Sum('payable_hours'),
            total_late_minutes=Sum('late_minutes'),
            total_undertime_minutes=Sum('undertime_minutes'),
        )

        days_present = attendance.filter(time_in__isnull=False).count()

        context = dict(
            self.admin_site.each_context(request),
            title='Attendance Summary',
            form=form,
            attendance=attendance,
            summary={
                'days_present': days_present,
                'total_payable_hours': totals['total_payable_hours'] or 0,
                'total_late_minutes': totals['total_late_minutes'] or 0,
                'total_undertime_minutes': totals['total_undertime_minutes'] or 0,
            },
        )

        return TemplateResponse(
            request,
            'admin/attendance/attendance/summary.html',
            context
        )