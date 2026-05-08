from datetime import timedelta, datetime
from decimal import Decimal
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

    list_display = (
        'employee_id_display',
        'employee_link',
        'start_date',
        'end_date',
        'total_payable_hours',
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
        '-start_date',
    )

    readonly_fields = (
        'total_payable_hours',
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
        url = reverse(
            'admin:payroll_payroll_change',
            args=[obj.id]
        )

        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.employee.full_name
        )

    employee_link.short_description = 'Employee Name'
    employee_link.admin_order_field = 'employee__last_name'

    def weekly_summary_link(self, request):
        url = reverse('admin:payroll-weekly-summary')

        return format_html(
            '<a class="button" href="{}" '
            'style="padding:8px 12px; background:#417690; '
            'color:white; border-radius:4px;">'
            'View Weekly Payroll Summary</a>',
            url
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        extra_context['weekly_summary_link'] = (
            self.weekly_summary_link(request)
        )

        return super().changelist_view(
            request,
            extra_context
        )

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                'weekly-summary/',
                self.admin_site.admin_view(
                    self.weekly_summary_view
                ),
                name='payroll-weekly-summary',
            ),

            path(
                'weekly-summary/export/',
                self.admin_site.admin_view(
                    self.export_weekly_payroll_csv
                ),
                name='payroll-weekly-summary-export',
            ),

            path(
                'weekly-summary/save/',
                self.admin_site.admin_view(
                    self.save_payroll_period
                ),
                name='payroll-weekly-summary-save',
            ),
        ]

        return custom_urls + urls

    def get_payroll_range(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if start_date and end_date:
            start_date = datetime.strptime(
                start_date,
                '%Y-%m-%d'
            ).date()

            end_date = datetime.strptime(
                end_date,
                '%Y-%m-%d'
            ).date()

        else:
            today = timezone.localdate()

            start_date = (
                today - timedelta(days=today.weekday())
            )

            end_date = start_date + timedelta(days=5)

        return start_date, end_date

    def get_deliver_allowance(self, attendance_records):
        total = Decimal('0.00')
        deliver_days = 0

        for record in attendance_records:
            if not record.delivery_allowance_applicable:
                continue

            position = (
                record.employee.position.lower().strip()
            )

            deliver_days += 1

            if position == 'driver':
                total += DRIVER_DELIVER_ALLOWANCE

            elif position == 'helper':
                total += HELPER_DELIVER_ALLOWANCE

        return deliver_days, total

    def get_overtime_pay(self, attendance_records, daily_rate):
        overtime_minutes = 0
        overtime_pay = Decimal('0.00')

        overtime_rate_per_minute = (
            daily_rate
            / Decimal('8.00')
            / Decimal('60.00')
        )

        for record in attendance_records:
            minutes = record.overtime_minutes or 0

            overtime_minutes += minutes

            overtime_pay += (
                overtime_rate_per_minute
                * Decimal(minutes)
            )

        return overtime_minutes, overtime_pay

    def build_weekly_payroll_data(self, start_date, end_date):
        attendance = Attendance.objects.select_related(
            'employee'
        ).filter(
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
                total_undertime_minutes=Sum(
                    'undertime_minutes'
                ),
                total_overtime_minutes=Sum(
                    'overtime_minutes'
                ),
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
        }

        for row in payroll_data:
            hours = (
                row['total_payable_hours']
                or Decimal('0.00')
            )

            daily_rate = (
                row['employee__rate']
                or Decimal('0.00')
            )

            benefits = (
                row['employee__benefits']
                or Decimal('0.00')
            )

            hourly_rate = (
                daily_rate / Decimal('8.00')
            )

            base_salary = hours * hourly_rate

            employee_attendance_records = (
                Attendance.objects
                .select_related('employee')
                .filter(
                    employee_id=row['employee__id'],
                    date__range=[start_date, end_date],
                    time_in__isnull=False,
                )
            )

            overtime_minutes, overtime_pay = (
                self.get_overtime_pay(
                    employee_attendance_records,
                    daily_rate
                )
            )

            deliver_days, deliver_allowance = (
                self.get_deliver_allowance(
                    employee_attendance_records
                )
            )

            transportation_days = (
                employee_attendance_records
                .filter(
                    transportation_fee_applicable=True
                )
                .count()
            )

            transportation_fee = (
                Decimal(transportation_days)
                * TRANSPORTATION_FEE_PER_DAY
            )

            final_salary = (
                base_salary
                + overtime_pay
                + deliver_allowance
                + transportation_fee
                - benefits
            )

            row.update({
                'daily_rate': daily_rate,
                'hourly_rate': hourly_rate,
                'base_salary': base_salary,
                'overtime_minutes': overtime_minutes,
                'overtime_pay': overtime_pay,
                'benefits': benefits,
                'deliver_days': deliver_days,
                'deliver_allowance': deliver_allowance,
                'transportation_days': transportation_days,
                'transportation_fee': transportation_fee,
                'total_salary': final_salary,
            })

        return payroll_data, totals

    def save_payroll_period(self, request):
        start_date, end_date = (
            self.get_payroll_range(request)
        )

        payroll_data, totals = (
            self.build_weekly_payroll_data(
                start_date,
                end_date
            )
        )

        created_count = 0
        updated_count = 0

        for row in payroll_data:
            employee = Employee.objects.get(
                id=row['employee__id']
            )

            payroll, created = (
                Payroll.objects.get_or_create(
                    employee=employee,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

            payroll.save()

            if created:
                created_count += 1
            else:
                updated_count += 1

        messages.success(
            request,
            f'Payroll saved for '
            f'{start_date} to {end_date}. '
            f'Created: {created_count}, '
            f'Updated: {updated_count}.'
        )

        return redirect(
            f"{reverse('admin:payroll_payroll_changelist')}"
        )

    def weekly_summary_view(self, request):
        start_date, end_date = (
            self.get_payroll_range(request)
        )

        payroll_data, totals = (
            self.build_weekly_payroll_data(
                start_date,
                end_date
            )
        )

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
        start_date, end_date = (
            self.get_payroll_range(request)
        )

        payroll_data, totals = (
            self.build_weekly_payroll_data(
                start_date,
                end_date
            )
        )

        response = HttpResponse(
            content_type='text/csv'
        )

        response[
            'Content-Disposition'
        ] = 'attachment; filename="payroll_summary.csv"'

        writer = csv.writer(response)

        writer.writerow([
            f'Payroll Period: {start_date} to {end_date}'
        ])

        writer.writerow([])