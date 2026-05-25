from django.shortcuts import render
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
        employees = employees.filter(employment_status=status_filter)

    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(employment_status="ACTIVE").count()
    resigned_employees = Employee.objects.filter(employment_status="RESIGNED").count()
    mia_employees = Employee.objects.filter(employment_status="MIA").count()
    terminated_employees = Employee.objects.filter(employment_status="TERMINATED").count()

    active_rates = Employee.objects.filter(
        employment_status="ACTIVE"
    ).exclude(rate__isnull=True)

    if active_rates.exists():
        average_rate = sum(employee.rate for employee in active_rates) / active_rates.count()
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

    return render(request, "dashboard/employees_page.html", context)