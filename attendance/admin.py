from datetime import timedelta
from decimal import Decimal
import csv

from django.http import HttpResponse
from django.contrib import admin
from django.db.models import Sum, Count
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Attendance, PayrollAdjustment
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
            '<a class="button" href="{}" style="padding:8px 12px; background:#417690; color:white; border-radius:4px;">View Weekly Payroll Summary</a>',
            url
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['summary_link'] = self.summary_link(request)
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('summary/', self.admin_site.admin_view(self.summary_view), name='attendance-attendance-summary'),
            path('export/', self.admin_site.admin_view(self.export_payroll_csv), name='attendance-export-payroll'),
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
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            if employee:
                attendance = attendance.filter(employee=employee)

            if week_date:
                week_start = week_date - timedelta(days=week_date.weekday())
                week_end = week_start + timedelta(days=5)
                attendance = attendance.filter(date__range=[week_start, week_end])
                period_label = f"Weekly Payroll: {week_start} to {week_end}"

            elif start_date and end_date:
                attendance = attendance.filter(date__range=[start_date, end_date])
                period_label = f"{start_date} to {end_date}"

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
        )

        totals = {
            'grand_total_salary': Decimal('0.00'),
            'grand_base_salary': Decimal('0.00'),
            'grand_benefits': Decimal('0.00'),
            'grand_cash_advance': Decimal('0.00'),
            'grand_charges': Decimal('0.00'),
            'grand_rent': Decimal('0.00'),
            'days_present': 0,
            'total_payable_hours': Decimal('0.00'),
            'total_late_minutes': 0,
            'total_undertime_minutes': 0,
        }

        for row in payroll_data:
            emp_id = row['employee__id']

            hours = row['total_payable_hours'] or Decimal('0')
            daily_rate = row['employee__rate'] or Decimal('0')
            hourly_rate = daily_rate / Decimal('8')
            base_salary = hours * hourly_rate

            adjustments = PayrollAdjustment.objects.filter(employee_id=emp_id)

            if week_start and week_end:
                adjustments = adjustments.filter(date__range=[week_start, week_end])

            benefits = adjustments.filter(adjustment_type='benefit').aggregate(total=Sum('amount'))['total'] or Decimal('0')
            cash_advance = adjustments.filter(adjustment_type='cash_advance').aggregate(total=Sum('amount'))['total'] or Decimal('0')
            charges = adjustments.filter(adjustment_type='charge').aggregate(total=Sum('amount'))['total'] or Decimal('0')
            rent = adjustments.filter(adjustment_type='rent').aggregate(total=Sum('amount'))['total'] or Decimal('0')

            final_salary = base_salary + benefits - cash_advance - charges - rent

            row.update({
                'daily_rate': daily_rate,
                'hourly_rate': hourly_rate,
                'base_salary': base_salary,
                'benefits': benefits,
                'cash_advance': cash_advance,
                'charges': charges,
                'rent': rent,
                'total_salary': final_salary,
            })

            totals['grand_total_salary'] += final_salary
            totals['grand_base_salary'] += base_salary
            totals['grand_benefits'] += benefits
            totals['grand_cash_advance'] += cash_advance
            totals['grand_charges'] += charges
            totals['grand_rent'] += rent
            totals['days_present'] += row['days_present'] or 0
            totals['total_payable_hours'] += hours
            totals['total_late_minutes'] += row['total_late_minutes'] or 0
            totals['total_undertime_minutes'] += row['total_undertime_minutes'] or 0

        context = dict(
            self.admin_site.each_context(request),
            form=form,
            payroll_data=payroll_data,
            period_label=period_label,
            week_start=week_start,
            week_end=week_end,
            totals=totals,
        )

        return TemplateResponse(request, 'admin/attendance/attendance/summary.html', context)

    def export_payroll_csv(self, request):
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
            )
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payroll.csv"'
        writer = csv.writer(response)

        writer.writerow([period_label])
        writer.writerow([
            'Employee ID', 'Name', 'Hours', 'Base Salary',
            'Benefits', 'Cash Advance', 'Charges', 'Rent', 'Final Salary'
        ])

        for row in payroll_data:
            emp_id = row['employee__id']

            hours = row['total_payable_hours'] or Decimal('0')
            rate = row['employee__rate'] or Decimal('0')
            base_salary = hours * (rate / Decimal('8'))

            adjustments = PayrollAdjustment.objects.filter(employee_id=emp_id)

            if week_start and week_end:
                adjustments = adjustments.filter(date__range=[week_start, week_end])

            benefits = adjustments.filter(adjustment_type='benefit').aggregate(total=Sum('amount'))['total'] or 0
            cash_advance = adjustments.filter(adjustment_type='cash_advance').aggregate(total=Sum('amount'))['total'] or 0
            charges = adjustments.filter(adjustment_type='charge').aggregate(total=Sum('amount'))['total'] or 0
            rent = adjustments.filter(adjustment_type='rent').aggregate(total=Sum('amount'))['total'] or 0

            final_salary = base_salary + benefits - cash_advance - charges - rent

            writer.writerow([
                row['employee__employee_id'],
                f"{row['employee__first_name']} {row['employee__last_name']}",
                hours,
                base_salary,
                benefits,
                cash_advance,
                charges,
                rent,
                final_salary
            ])

        return response