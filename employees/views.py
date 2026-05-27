from decimal import Decimal

from django.shortcuts import render
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce

from rest_framework import viewsets

from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().order_by("-id")
    serializer_class = EmployeeSerializer


def employees_page(request):

    status_filter = request.GET.get("status", "ALL")

    employees = Employee.objects.all().order_by("employee_id")

    if status_filter != "ALL":
        employees = employees.filter(
            employment_status=status_filter
        )

    employees = employees.annotate(
        attendance_count=Count(
            "attendances",
            distinct=True
        ),
        payroll_count=Count(
            "payrolls",
            distinct=True
        ),
        total_cash_advance=Coalesce(
            Sum("payrolls__cash_advance"),
            Decimal("0.00")
        ),
        total_charges_amount=Coalesce(
            Sum("payrolls__charges"),
            Decimal("0.00")
        ),
        total_rent=Coalesce(
            Sum("payrolls__rent"),
            Decimal("0.00")
        ),
        total_benefits=Coalesce(
            Sum("payrolls__benefits"),
            Decimal("0.00")
        ),
    )

    total_employees = Employee.objects.count()

    active_employees = Employee.objects.filter(
        employment_status="ACTIVE"
    ).count()

    resigned_employees = Employee.objects.filter(
        employment_status="RESIGNED"
    ).count()

    mia_employees = Employee.objects.filter(
        employment_status="MIA"
    ).count()

    terminated_employees = Employee.objects.filter(
        employment_status="TERMINATED"
    ).count()

    active_rates = Employee.objects.filter(
        employment_status="ACTIVE"
    ).exclude(
        rate__isnull=True
    )

    if active_rates.exists():
        average_rate = (
            sum(employee.rate for employee in active_rates)
            / active_rates.count()
        )
    else:
        average_rate = 0

    context = {
        "employees": employees,
        "status_filter": status_filter,
        "total_employees": total_employees,
        "active_employees": active_employees,
        "resigned_employees": resigned_employees,
        "mia_employees": mia_employees,
        "terminated_employees": terminated_employees,
        "average_rate": average_rate,
    }

    return render(
        request,
        "dashboard/employees_page.html",
        context
    )

def view_employee_page_view(request, employee_id):

    employee = get_object_or_404(
        Employee,
        id=employee_id
    )

    attendances = employee.attendances.all().order_by("-date")[:10]
    payrolls = employee.payrolls.all().order_by("-start_date")[:10]

    total_charges = 0

    for payroll in payrolls:
        total_charges += (
            payroll.benefits
            + payroll.cash_advance
            + payroll.charges
            + payroll.rent
        )

    context = {
        "employee": employee,
        "attendances": attendances,
        "payrolls": payrolls,
        "attendance_count": employee.attendances.count(),
        "payroll_count": employee.payrolls.count(),
        "total_charges": total_charges,
    }

    return render(
        request,
        "dashboard/view_employee_page.html",
        context
    )