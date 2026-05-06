from datetime import timedelta, datetime
from decimal import Decimal
import csv

from django.contrib import admin
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from attendance.models import Attendance
from .models import Payroll, PayrollAdjustment


TRANSPORTATION_FEE_PER_DAY = Decimal('15.00')
DRIVER_DELIVER_ALLOWANCE = Decimal('200.00')
HELPER_DELIVER_ALLOWANCE = Decimal('150.00')


@admin.register(PayrollAdjustment)
class PayrollAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'date',
        'adjustment_type',
        'amount',
        'description',
    )

    list_filter = (
        'adjustment_type',
        'date',
        'employee',
    )

    search_fields = (
        'employee__employee_id',
        'employee__first_name',
        'employee__last_name',
    )


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'start_date',
        'end_date',
        'total_payable_hours',
        'base_salary',
        'benefits',
        'allowance',
        'cash_advance',
        'charges',
        'rent',
        'total_salary',
        'created_at',
    )

    list_filter = (
        'start_date',
        'end_date',
        'employee',
    )

    search_fields = (
        'employee__employee_id',
        'employee__first_name',
        'employee__last_name',
    )

    readonly_fields = (
        'total_payable_hours',
        'base_salary',
        'benefits',
        'allowance',
        'cash_advance',
        'charges',
        'rent',
        'total_salary',
        'created_at',
    )

    def weekly_summary_link(self, request):
        url = reverse('admin:payroll-weekly-summary')
        return format_html(
            '<a class="button" href="{}" style="padding:8px 12px; background:#417690; color:white; border-radius:4px;">View Weekly Payroll Summary</a>',
            url
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['weekly_summary_link'] = self.weekly_summary_link(request)
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'weekly-summary/',
                self.admin_site.admin_view(self.weekly_summary_view),
                name='payroll-weekly-summary',
            ),
            path(
                'weekly-summary/export/',
                self.admin_site.admin_view(self.export_weekly_payroll_csv),
                name='payroll-weekly-summary-export',
            ),
        ]
        return custom_urls + urls

    def get_payroll_range(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            today = timezone.localdate()
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=5)

        return start_date, end_date

    def get_deliver_allowance(self, attendance_records):
        total = Decimal('0.00')
        deliver_days = 0

        for record in attendance_records:
            position = record.employee.position.lower().strip()

            if record.work_type == 'deliver':
                deliver_days += 1

                if position == 'driver':
                    total += DRIVER_DELIVER_ALLOWANCE
                elif position == 'helper':
                    total += HELPER_DELIVER_ALLOWANCE

        return deliver_days, total

    def build_weekly_payroll_data(self, start_date, end_date):
        attendance = Attendance.objects.select_related('employee').filter(
            date__range=[start_date, end_date]
        )

        payroll_data = (
            attendance
            .values(
                'employee__id',
                'employee__employee_id',
                'employee__first_name',
                'employee__last_name',
                'employee__position',
                'employee__rate',
                'employee__benefits',
            )
            .annotate(
                days_present=Count('id'),
                total_payable_hours=Sum('payable_hours'),
                total_late_minutes=Sum('late_minutes'),
                total_undertime_minutes=Sum('undertime_minutes'),
            )
            .order_by('employee__employee_id')
        )

        totals = {
            'days_present': 0,
            'total_payable_hours': Decimal('0.00'),
            'total_late_minutes': 0,
            'total_undertime_minutes': 0,
            'grand_base_salary': Decimal('0.00'),
            'grand_benefits': Decimal('0.00'),
            'grand_manual_allowance': Decimal('0.00'),
            'grand_deliver_allowance': Decimal('0.00'),
            'grand_transportation_fee': Decimal('0.00'),
            'grand_cash_advance': Decimal('0.00'),
            'grand_charges': Decimal('0.00'),
            'grand_rent': Decimal('0.00'),
            'grand_total_salary': Decimal('0.00'),
        }

        for row in payroll_data:
            employee_id = row['employee__id']

            hours = row['total_payable_hours'] or Decimal('0.00')
            daily_rate = row['employee__rate'] or Decimal('0.00')
            benefits = row['employee__benefits'] or Decimal('0.00')

            hourly_rate = daily_rate / Decimal('8.00')
            base_salary = hours * hourly_rate

            employee_attendance_records = Attendance.objects.select_related('employee').filter(
                employee_id=employee_id,
                date__range=[start_date, end_date],
                time_in__isnull=False,
            )

            deliver_days, deliver_allowance = self.get_deliver_allowance(
                employee_attendance_records
            )

            transportation_days = employee_attendance_records.filter(
                transportation_fee_applicable=True,
            ).count()

            transportation_fee = Decimal(transportation_days) * TRANSPORTATION_FEE_PER_DAY

            adjustments = PayrollAdjustment.objects.filter(
                employee_id=employee_id,
                date__range=[start_date, end_date]
            )

            manual_allowance = adjustments.filter(
                adjustment_type='allowance'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            cash_advance = adjustments.filter(
                adjustment_type='cash_advance'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            charges = adjustments.filter(
                adjustment_type='charge'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            rent = adjustments.filter(
                adjustment_type='rent'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            total_allowance = manual_allowance + deliver_allowance

            final_salary = (
                base_salary
                + total_allowance
                + transportation_fee
                - benefits
                - cash_advance
                - charges
                - rent
            )

            row.update({
                'daily_rate': daily_rate,
                'hourly_rate': hourly_rate,
                'base_salary': base_salary,
                'benefits': benefits,
                'manual_allowance': manual_allowance,
                'deliver_days': deliver_days,
                'deliver_allowance': deliver_allowance,
                'total_allowance': total_allowance,
                'transportation_days': transportation_days,
                'transportation_fee': transportation_fee,
                'cash_advance': cash_advance,
                'charges': charges,
                'rent': rent,
                'total_salary': final_salary,
            })

            totals['days_present'] += row['days_present'] or 0
            totals['total_payable_hours'] += hours
            totals['total_late_minutes'] += row['total_late_minutes'] or 0
            totals['total_undertime_minutes'] += row['total_undertime_minutes'] or 0
            totals['grand_base_salary'] += base_salary
            totals['grand_benefits'] += benefits
            totals['grand_manual_allowance'] += manual_allowance
            totals['grand_deliver_allowance'] += deliver_allowance
            totals['grand_transportation_fee'] += transportation_fee
            totals['grand_cash_advance'] += cash_advance
            totals['grand_charges'] += charges
            totals['grand_rent'] += rent
            totals['grand_total_salary'] += final_salary

        return payroll_data, totals

    def weekly_summary_view(self, request):
        start_date, end_date = self.get_payroll_range(request)
        payroll_data, totals = self.build_weekly_payroll_data(start_date, end_date)

        context = dict(
            self.admin_site.each_context(request),
            title='Payroll Summary',
            start_date=start_date,
            end_date=end_date,
            payroll_data=payroll_data,
            totals=totals,
        )

        return TemplateResponse(
            request,
            'admin/payroll/weekly_summary.html',
            context
        )

    def export_weekly_payroll_csv(self, request):
        start_date, end_date = self.get_payroll_range(request)
        payroll_data, totals = self.build_weekly_payroll_data(start_date, end_date)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payroll_summary.csv"'

        writer = csv.writer(response)

        writer.writerow([f'Payroll Period: {start_date} to {end_date}'])
        writer.writerow([])

        writer.writerow([
            'Employee ID',
            'Name',
            'Position',
            'Days Present',
            'Total Payable Hours',
            'Late Minutes',
            'Undertime Minutes',
            'Daily Rate',
            'Hourly Rate',
            'Base Salary',
            'Benefits/Deductions',
            'Manual Allowance',
            'Deliver Days',
            'Deliver Allowance',
            'Total Allowance',
            'Transportation Days',
            'Transportation Fee',
            'Cash Advance',
            'Charges',
            'Rent',
            'Final Salary',
        ])

        for row in payroll_data:
            writer.writerow([
                row['employee__employee_id'],
                f"{row['employee__first_name']} {row['employee__last_name']}",
                row['employee__position'],
                row['days_present'] or 0,
                row['total_payable_hours'] or 0,
                row['total_late_minutes'] or 0,
                row['total_undertime_minutes'] or 0,
                row['daily_rate'],
                row['hourly_rate'],
                row['base_salary'],
                row['benefits'],
                row['manual_allowance'],
                row['deliver_days'],
                row['deliver_allowance'],
                row['total_allowance'],
                row['transportation_days'],
                row['transportation_fee'],
                row['cash_advance'],
                row['charges'],
                row['rent'],
                row['total_salary'],
            ])

        return response