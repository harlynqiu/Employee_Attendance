from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from employees.models import Employee
from attendance.models import Attendance


TRANSPORTATION_FEE_PER_DAY = Decimal('15.00')
DRIVER_DELIVER_ALLOWANCE = Decimal('200.00')
HELPER_DELIVER_ALLOWANCE = Decimal('150.00')


class PayrollAdjustment(models.Model):
    ADJUSTMENT_TYPE = (
        ('allowance', 'Allowance'),
        ('cash_advance', 'Cash Advance'),
        ('charge', 'Charge'),
        ('rent', 'Rent'),
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='payroll_adjustments'
    )

    date = models.DateField(default=timezone.localdate)

    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    description = models.CharField(max_length=255, blank=True, null=True)

    is_deducted = models.BooleanField(
        default=False,
        help_text='For future payroll correction use only.'
    )

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({'amount': 'Amount must be greater than 0.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.employee_id} - {self.get_adjustment_type_display()} - {self.amount}"


class Payroll(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='payrolls'
    )

    start_date = models.DateField()
    end_date = models.DateField()

    total_payable_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transportation_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    benefits = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    allowance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Manual allowance for this payroll period.'
    )

    cash_advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    remarks = models.TextField(blank=True, null=True)

    total_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date', 'employee__last_name']

    def money(self, value):
        return Decimal(value or 0).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError({
                'end_date': 'End date cannot be earlier than start date.'
            })

    def compute_delivery_allowance(self, attendance_records):
        total = Decimal('0.00')

        for record in attendance_records:
            if not record.delivery_allowance_applicable:
                continue

            position = record.employee.position.lower().strip()

            if position == 'driver':
                total += DRIVER_DELIVER_ALLOWANCE
            elif position == 'helper':
                total += HELPER_DELIVER_ALLOWANCE

        return self.money(total)

    def compute_overtime_pay(self, attendance_records):
        total = Decimal('0.00')
        daily_rate = self.employee.rate or Decimal('0.00')

        overtime_rate_per_minute = daily_rate / Decimal('8.00') / Decimal('60.00')

        for record in attendance_records:
            overtime_minutes = Decimal(record.overtime_minutes or 0)
            total += overtime_rate_per_minute * overtime_minutes

        return self.money(total)

    def save(self, *args, **kwargs):
        self.full_clean()

        attendance = Attendance.objects.filter(
            employee=self.employee,
            date__range=[self.start_date, self.end_date]
        )

        total_hours = attendance.aggregate(
            total=Sum('payable_hours')
        )['total'] or Decimal('0.00')

        daily_rate = self.employee.rate or Decimal('0.00')
        hourly_rate = daily_rate / Decimal('8.00')

        base_salary = total_hours * hourly_rate
        overtime_pay = self.compute_overtime_pay(attendance)

        transportation_days = attendance.filter(
            transportation_fee_applicable=True
        ).count()

        transportation_fee = Decimal(transportation_days) * TRANSPORTATION_FEE_PER_DAY
        delivery_allowance = self.compute_delivery_allowance(attendance)
        benefits = self.employee.benefits or Decimal('0.00')

        allowance = self.allowance or Decimal('0.00')
        cash_advance = self.cash_advance or Decimal('0.00')
        charges = self.charges or Decimal('0.00')
        rent = self.rent or Decimal('0.00')

        total_salary = (
            base_salary
            + overtime_pay
            + transportation_fee
            + delivery_allowance
            + allowance
            - benefits
            - cash_advance
            - charges
            - rent
        )

        self.total_payable_hours = self.money(total_hours)
        self.base_salary = self.money(base_salary)
        self.overtime_pay = self.money(overtime_pay)
        self.transportation_fee = self.money(transportation_fee)
        self.delivery_allowance = self.money(delivery_allowance)
        self.benefits = self.money(benefits)
        self.allowance = self.money(allowance)
        self.cash_advance = self.money(cash_advance)
        self.charges = self.money(charges)
        self.rent = self.money(rent)
        self.total_salary = self.money(total_salary)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.employee_id} | {self.start_date} to {self.end_date}"