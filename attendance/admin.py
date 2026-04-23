from datetime import timedelta
import csv

from django.http import HttpResponse
from django.contrib import admin
from django.db.models import Sum, Count
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
            '<a class="button" href="{}" style="padding:8px 12px; background:#417690; color:white; border-radius:4px; text-decoration:none;">View Weekly Payroll Summary</a>',
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
            path(
                'export/',
                self.admin_site.admin_view(self.export_payroll_csv),
                name='attendance-export-payroll',
            ),
        ]
        return custom_urls + urls

    def get_filtered_attendance(self, request):
        form = AttendanceSummaryForm(request.GET or None)
        attendance = Attendance.objects.select_related('employee').all()

        week_start = None
        week_end = None
        period_label = 'All Records'

        if form.is_valid():
            employee = form.cleaned_data.get('employee')
            week_date = form.cleaned_data.get('week_date')
            year = form.cleaned_data.get('year')
            month = form.cleaned_data.get('month')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            if employee:
                attendance = attendance.filter(employee=employee)

            if week_date:
                week_start = week_date - timedelta(days=week_date.weekday())   # Monday
                week_end = week_start + timedelta(days=5)                      # Saturday
                attendance = attendance.filter(date__range=[week_start, week_end])
                period_label = f"Weekly Payroll: {week_start} to {week_end}"

            elif year and month:
                attendance = attendance.filter(date__year=year, date__month=month)
                period_label = f"Monthly View: {year}-{month:02d}"

            elif start_date and end_date:
                attendance = attendance.filter(date__range=[start_date, end_date])
                period_label = f"Custom Range: {start_date} to {end_date}"
            elif start_date:
                attendance = attendance.filter(date__gte=start_date)
                period_label = f"From {start_date}"
            elif end_date:
                attendance = attendance.filter(date__lte=end_date)
                period_label = f"Up to {end_date}"

        return form, attendance, week_start, week_end, period_label

    def summary_view(self, request):
        form, attendance, week_start, week_end, period_label = self.get_filtered_attendance(request)

        payroll_data = (
            attendance
            .values(
                'employee__id',
                'employee__employee_id',
                'employee__first_name',
                'employee__last_name',
                'employee__rate',
            )
            .annotate(
                days_present=Count('id'),
                total_payable_hours=Sum('payable_hours'),
                total_late_minutes=Sum('late_minutes'),
                total_undertime_minutes=Sum('undertime_minutes'),
            )
            .order_by('employee__last_name', 'employee__first_name')
        )

        grand_total_salary = 0
        grand_total_hours = 0
        grand_total_late = 0
        grand_total_undertime = 0
        grand_total_days = 0

        for row in payroll_data:
            hours = row['total_payable_hours'] or 0
            rate = row['employee__rate'] or 0
            row['total_salary'] = hours * rate

            grand_total_salary += row['total_salary']
            grand_total_hours += hours
            grand_total_late += row['total_late_minutes'] or 0
            grand_total_undertime += row['total_undertime_minutes'] or 0
            grand_total_days += row['days_present'] or 0

        context = dict(
            self.admin_site.each_context(request),
            title='Weekly Payroll Summary',
            form=form,
            payroll_data=payroll_data,
            week_start=week_start,
            week_end=week_end,
            period_label=period_label,
            totals={
                'days_present': grand_total_days,
                'total_payable_hours': grand_total_hours,
                'total_late_minutes': grand_total_late,
                'total_undertime_minutes': grand_total_undertime,
                'grand_total_salary': grand_total_salary,
            },
        )

        return TemplateResponse(
            request,
            'admin/attendance/attendance/summary.html',
            context
        )

    def export_payroll_csv(self, request):
        form, attendance, week_start, week_end, period_label = self.get_filtered_attendance(request)

        payroll_data = (
            attendance
            .values(
                'employee__employee_id',
                'employee__first_name',
                'employee__last_name',
                'employee__rate',
            )
            .annotate(
                days_present=Count('id'),
                total_payable_hours=Sum('payable_hours'),
                total_late_minutes=Sum('late_minutes'),
                total_undertime_minutes=Sum('undertime_minutes'),
            )
            .order_by('employee__last_name', 'employee__first_name')
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="weekly_payroll.csv"'

        writer = csv.writer(response)

        writer.writerow([period_label])
        writer.writerow([])

        writer.writerow([
            'Employee ID',
            'Name',
            'Days Present',
            'Total Payable Hours',
            'Total Late Minutes',
            'Total Undertime Minutes',
            'Salary Rate',
            'Total Salary',
        ])

        grand_total_salary = 0

        for row in payroll_data:
            hours = row['total_payable_hours'] or 0
            rate = row['employee__rate'] or 0
            salary = hours * rate
            grand_total_salary += salary

            writer.writerow([
                row['employee__employee_id'],
                f"{row['employee__first_name']} {row['employee__last_name']}",
                row['days_present'] or 0,
                hours,
                row['total_late_minutes'] or 0,
                row['total_undertime_minutes'] or 0,
                rate,
                salary,
            ])

        writer.writerow([])
        writer.writerow(['', '', '', '', '', '', 'Grand Total Salary', grand_total_salary])

        return response