from decimal import Decimal
from django.db.models import Sum
from attendance.models import Attendance


def compute_employee_payroll(employee, start_date, end_date):
    attendance = Attendance.objects.filter(
        employee=employee,
        date__range=[start_date, end_date]
    )

    total_payable_hours = attendance.aggregate(
        total=Sum('payable_hours')
    )['total'] or Decimal('0.00')

    total_salary = Decimal(total_payable_hours) * Decimal(employee.rate)

    return {
        'total_payable_hours': total_payable_hours,
        'total_salary': total_salary,
    }