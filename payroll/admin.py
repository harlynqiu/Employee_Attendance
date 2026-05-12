from datetime import timedelta, datetime
from decimal import Decimal, ROUND_HALF_UP
import csv

from django.contrib import admin, messages
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from attendance.models import Attendance
from employees.models import Employee
from .models import Payroll, PayrollAdjustment


TRANSPORTATION_FEE_PER_DAY = Decimal('15.00')
DRIVER_DELIVER_ALLOWANCE = Decimal('200.00')
HELPER_DELIVER_ALLOWANCE = Decimal('150.00')


def money(value):
    return Decimal(value or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def whole_number(value):
    return Decimal(value or 0).quantize(Decimal('1'), rounding=ROUND_HALF_UP)


def get_cash_breakdown(amount):
    denominations = [
        Decimal('100'),
        Decimal('50'),
        Decimal('20'),
        Decimal('10'),
        Decimal('5'),
        Decimal('1'),
        Decimal('0.25'),
    ]

    remaining = Decimal(amount or 0).quantize(
        Decimal('0.25'),
        rounding=ROUND_HALF_UP
    )

    breakdown = {}

    for denom in denominations:
        count = int(remaining // denom)
        breakdown[str(denom)] = count
        remaining -= Decimal(count) * denom
        remaining = remaining.quantize(Decimal('0.25'), rounding=ROUND_HALF_UP)

    return breakdown


@admin.register(PayrollAdjustment)
class PayrollAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'date',
        'adjustment_type',
        'amount',
        'is_deducted',
        'description',
    )

    list_filter = (
        'adjustment_type',
        'is_deducted',
        'date',
        'employee',
    )

    search_fields = (
        'employee__employee_id',
        'employee__first_name',
        'employee__last_name',
        'description',
    )

    ordering = (
        'employee__employee_id',
        '-date',
    )


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):

    change_list_template = 'admin/payroll/change_list.html'

    list_display = (
        'employee_id_display',
        'employee_link',
        'start_date',
        'end_date',
        'total_payable_hours',
        'total_late_minutes',
        'total_undertime_minutes',
        'base_salary',
        'overtime_pay',
        'transportation_fee',
        'delivery_allowance',
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

    ordering = (
        'employee__employee_id',
    )

    readonly_fields = (
        'total_payable_hours',
        'total_late_minutes',
        'total_undertime_minutes',
        'base_salary',
        'overtime_pay',
        'transportation_fee',
        'delivery_allowance',
        'benefits',
        'total_salary',
        'created_at',
    )

    fields = (
        'employee',
        'start_date',
        'end_date',
        'total_payable_hours',
        'total_late_minutes',
        'total_undertime_minutes',
        'base_salary',
        'overtime_pay',
        'transportation_fee',
        'delivery_allowance',
        'benefits',
        'allowance',
        'cash_advance',
        'charges',
        'rent',
        'remarks',
        'total_salary',
        'created_at',
    )

    def employee_id_display(self, obj):
        return obj.employee.employee_id

    employee_id_display.short_description = 'Employee ID'
    employee_id_display.admin_order_field = 'employee__employee_id'

    def employee_link(self, obj):
        url = reverse('admin:payroll_payroll_change', args=[obj.id])

        return format_html(
            '<a href="{}">{}, {}</a>',
            url,
            obj.employee.last_name,
            obj.employee.first_name
        )

    employee_link.short_description = 'Employee Name'
    employee_link.admin_order_field = 'employee__last_name'

    def changelist_view(self, request, extra_context=None):
        weekly_url = reverse('admin:payroll-weekly-summary')
        print_url = reverse('admin:payroll-payroll-print-all')

        extra_context = extra_context or {}

        extra_context['custom_buttons'] = format_html(
            '''
            <div style="display:flex; gap:10px; margin-bottom:15px;">
                <a class="button"
                   href="{}"
                   style="background:#417690; color:white; padding:10px 16px; border-radius:6px; text-decoration:none; font-weight:600;">
                   View Weekly Payroll Summary
                </a>

                <a class="button"
                   href="{}"
                   target="_blank"
                   style="background:#28a745; color:white; padding:10px 16px; border-radius:6px; text-decoration:none; font-weight:600;">
                   Print Payroll
                </a>
            </div>
            ''',
            weekly_url,
            print_url
        )

        return super().changelist_view(request, extra_context=extra_context)

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
            path(
                'weekly-summary/save/',
                self.admin_site.admin_view(self.save_payroll_period),
                name='payroll-weekly-summary-save',
            ),
            path(
                'print/',
                self.admin_site.admin_view(self.print_all_payroll_view),
                name='payroll-payroll-print-all',
            ),
            path(
                '<int:payroll_id>/print/',
                self.admin_site.admin_view(self.print_payroll_view),
                name='payroll-payroll-print',
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
            if not record.delivery_allowance_applicable:
                continue

            position = record.employee.position.lower().strip()
            deliver_days += 1

            if position == 'driver':
                total += DRIVER_DELIVER_ALLOWANCE
            elif position == 'helper':
                total += HELPER_DELIVER_ALLOWANCE

        return deliver_days, money(total)

    def get_overtime_pay(self, attendance_records, daily_rate):
        overtime_minutes = 0
        overtime_pay = Decimal('0.00')

        overtime_rate_per_minute = daily_rate / Decimal('8.00') / Decimal('60.00')

        for record in attendance_records:
            minutes = record.overtime_minutes or 0
            overtime_minutes += minutes
            overtime_pay += overtime_rate_per_minute * Decimal(minutes)

        return overtime_minutes, whole_number(overtime_pay)

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
                total_overtime_minutes=Sum('overtime_minutes'),
            )
            .order_by('employee__employee_id')
        )

        totals = {
            'days_present': 0,
            'total_payable_hours': Decimal('0.00'),
            'total_late_minutes': 0,
            'total_undertime_minutes': 0,
            'total_overtime_minutes': 0,
            'grand_base_salary': Decimal('0.00'),
            'grand_overtime_pay': Decimal('0.00'),
            'grand_benefits': Decimal('0.00'),
            'grand_deliver_allowance': Decimal('0.00'),
            'grand_transportation_fee': Decimal('0.00'),
            'grand_total_salary': Decimal('0.00'),

            'grand_cash_100': 0,
            'grand_cash_50': 0,
            'grand_cash_20': 0,
            'grand_cash_10': 0,
            'grand_cash_5': 0,
            'grand_cash_1': 0,
            'grand_cash_025': 0,
        }

        for row in payroll_data:
            hours = row['total_payable_hours'] or Decimal('0.00')
            daily_rate = row['employee__rate'] or Decimal('0.00')
            benefits = row['employee__benefits'] or Decimal('0.00')

            hourly_rate = daily_rate / Decimal('8.00')
            base_salary = money(hours * hourly_rate)

            employee_attendance_records = (
                Attendance.objects
                .select_related('employee')
                .filter(
                    employee_id=row['employee__id'],
                    date__range=[start_date, end_date],
                    time_in__isnull=False,
                )
            )

            overtime_minutes, overtime_pay = self.get_overtime_pay(
                employee_attendance_records,
                daily_rate
            )

            deliver_days, deliver_allowance = self.get_deliver_allowance(
                employee_attendance_records
            )

            transportation_days = (
                employee_attendance_records
                .filter(transportation_fee_applicable=True)
                .count()
            )

            transportation_fee = money(
                Decimal(transportation_days) * TRANSPORTATION_FEE_PER_DAY
            )

            final_salary = money(
                base_salary
                + overtime_pay
                + deliver_allowance
                + transportation_fee
                - benefits
            )

            cash = get_cash_breakdown(final_salary)

            row.update({
                'daily_rate': money(daily_rate),
                'hourly_rate': money(hourly_rate),
                'base_salary': base_salary,
                'overtime_minutes': overtime_minutes,
                'overtime_pay': overtime_pay,
                'benefits': money(benefits),
                'deliver_days': deliver_days,
                'deliver_allowance': deliver_allowance,
                'transportation_days': transportation_days,
                'transportation_fee': transportation_fee,
                'total_salary': final_salary,

                'cash_100': cash['100'],
                'cash_50': cash['50'],
                'cash_20': cash['20'],
                'cash_10': cash['10'],
                'cash_5': cash['5'],
                'cash_1': cash['1'],
                'cash_025': cash['0.25'],
            })

            totals['days_present'] += row['days_present'] or 0
            totals['total_payable_hours'] += hours
            totals['total_late_minutes'] += row['total_late_minutes'] or 0
            totals['total_undertime_minutes'] += row['total_undertime_minutes'] or 0
            totals['total_overtime_minutes'] += overtime_minutes
            totals['grand_base_salary'] += base_salary
            totals['grand_overtime_pay'] += overtime_pay
            totals['grand_benefits'] += money(benefits)
            totals['grand_deliver_allowance'] += deliver_allowance
            totals['grand_transportation_fee'] += transportation_fee
            totals['grand_total_salary'] += final_salary

            totals['grand_cash_100'] += cash['100']
            totals['grand_cash_50'] += cash['50']
            totals['grand_cash_20'] += cash['20']
            totals['grand_cash_10'] += cash['10']
            totals['grand_cash_5'] += cash['5']
            totals['grand_cash_1'] += cash['1']
            totals['grand_cash_025'] += cash['0.25']

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

    def save_payroll_period(self, request):
        start_date, end_date = self.get_payroll_range(request)

        payroll_data, totals = self.build_weekly_payroll_data(start_date, end_date)

        created_count = 0
        updated_count = 0

        for row in payroll_data:
            employee = Employee.objects.get(id=row['employee__id'])

            payroll, created = Payroll.objects.get_or_create(
                employee=employee,
                start_date=start_date,
                end_date=end_date,
            )

            payroll.save()

            if created:
                created_count += 1
            else:
                updated_count += 1

        messages.success(
            request,
            f'Payroll saved for {start_date} to {end_date}. '
            f'Created: {created_count}, Updated: {updated_count}.'
        )

        return redirect(reverse('admin:payroll_payroll_changelist'))

    def print_all_payroll_view(self, request):
        payrolls = Payroll.objects.select_related('employee').order_by(
            'employee__employee_id'
        )

        context = dict(
            self.admin_site.each_context(request),
            payrolls=payrolls,
            title='Print Payroll',
        )

        return TemplateResponse(
            request,
            'admin/payroll/payroll_print.html',
            context
        )

    def print_payroll_view(self, request, payroll_id):
        payroll = Payroll.objects.select_related('employee').get(id=payroll_id)

        context = dict(
            self.admin_site.each_context(request),
            payroll=payroll,
            payrolls=[payroll],
            title='Print Payroll',
        )

        return TemplateResponse(
            request,
            'admin/payroll/payroll_print.html',
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
            'Overtime Minutes',
            'Overtime Pay',
            'Daily Rate',
            'Hourly Rate',
            'Base Salary',
            'Benefits',
            'Deliver Days',
            'Deliver Allowance',
            'Transportation Days',
            'Transportation Fee',
            'Final Salary',
            '100',
            '50',
            '20',
            '10',
            '5',
            '1',
            '0.25',
        ])

        for row in payroll_data:
            writer.writerow([
                row['employee__employee_id'],
                f"{row['employee__last_name']}, {row['employee__first_name']}",
                row['employee__position'],
                row['days_present'] or 0,
                row['total_payable_hours'] or 0,
                row['total_late_minutes'] or 0,
                row['total_undertime_minutes'] or 0,
                row['overtime_minutes'] or 0,
                row['overtime_pay'],
                row['daily_rate'],
                row['hourly_rate'],
                row['base_salary'],
                row['benefits'],
                row['deliver_days'],
                row['deliver_allowance'],
                row['transportation_days'],
                row['transportation_fee'],
                row['total_salary'],
                row['cash_100'],
                row['cash_50'],
                row['cash_20'],
                row['cash_10'],
                row['cash_5'],
                row['cash_1'],
                row['cash_025'],
            ])

        writer.writerow([
            '',
            'TOTAL SALARY',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            totals['grand_total_salary'],
            totals['grand_cash_100'],
            totals['grand_cash_50'],
            totals['grand_cash_20'],
            totals['grand_cash_10'],
            totals['grand_cash_5'],
            totals['grand_cash_1'],
            totals['grand_cash_025'],
        ])

        writer.writerow([])
        writer.writerow(['CASH BREAKDOWN SUMMARY'])
        writer.writerow([])
        writer.writerow(['Denomination', 'Total Pieces Needed'])
        writer.writerow(['P100', totals['grand_cash_100']])
        writer.writerow(['P50', totals['grand_cash_50']])
        writer.writerow(['P20', totals['grand_cash_20']])
        writer.writerow(['P10', totals['grand_cash_10']])
        writer.writerow(['P5', totals['grand_cash_5']])
        writer.writerow(['P1', totals['grand_cash_1']])
        writer.writerow(['P0.25', totals['grand_cash_025']])

        return response