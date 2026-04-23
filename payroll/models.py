from decimal import Decimal
from django.db import models
from employees.models import Employee
from .utils import compute_employee_payroll


class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    start_date = models.DateField()
    end_date = models.DateField()

    total_payable_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        payroll_data = compute_employee_payroll(
            self.employee,
            self.start_date,
            self.end_date
        )

        self.total_payable_hours = payroll_data['total_payable_hours']
        self.total_salary = payroll_data['total_salary']

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.employee_id} | {self.start_date} to {self.end_date}"