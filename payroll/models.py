from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from employees.models import Employee
from attendance.models import Attendance


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

    benefits = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cash_advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    total_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date', 'employee__last_name']

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError({'end_date': 'End date cannot be earlier than start date.'})

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

        adjustments = PayrollAdjustment.objects.filter(
            employee=self.employee,
            date__range=[self.start_date, self.end_date]
        )

        allowance = adjustments.filter(
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

        benefits = self.employee.benefits or Decimal('0.00')

        total_salary = (
            base_salary
            + allowance
            - benefits
            - cash_advance
            - charges
            - rent
        )

        self.total_payable_hours = total_hours
        self.base_salary = base_salary
        self.benefits = benefits
        self.allowance = allowance
        self.cash_advance = cash_advance
        self.charges = charges
        self.rent = rent
        self.total_salary = total_salary

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.employee_id} | {self.start_date} to {self.end_date}"