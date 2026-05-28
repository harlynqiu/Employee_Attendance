from decimal import Decimal
from django.shortcuts import redirect

from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce

from rest_framework import viewsets

from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().order_by("-id")
    serializer_class = EmployeeSerializer


def employees_page(request):
    status_filter = request.GET.get("status", "ALL")
    q = request.GET.get("q", "").strip()

    employees = Employee.objects.all().order_by("employee_id")

    if status_filter != "ALL":
        employees = employees.filter(
            employment_status=status_filter
        )

    if q:
        employees = employees.filter(
            Q(employee_id__icontains=q) |
            Q(first_name__icontains=q) |
            Q(middle_initial__icontains=q) |
            Q(last_name__icontains=q) |
            Q(position__icontains=q) |
            Q(contact_number__icontains=q)
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
        average_rate = Decimal("0.00")

    context = {
        "employees": employees,
        "status_filter": status_filter,
        "q": q,
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

    total_charges = Decimal("0.00")

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

def new_employee_page(request):
    if request.method == "POST":
        employee = Employee(
            first_name=request.POST.get("first_name", "").strip(),
            middle_initial=request.POST.get("middle_initial", "").strip(),
            last_name=request.POST.get("last_name", "").strip(),
            date_of_birth=request.POST.get("date_of_birth") or None,
            citizenship=request.POST.get("citizenship", "").strip(),
            address=request.POST.get("address", "").strip(),
            contact_number=request.POST.get("contact_number", "").strip(),
            spouse_name=request.POST.get("spouse_name", "").strip(),
            spouse_contact_number=request.POST.get("spouse_contact_number", "").strip(),

            elementary=request.POST.get("elementary", "").strip(),
            elementary_year=request.POST.get("elementary_year", "").strip(),
            high_school=request.POST.get("high_school", "").strip(),
            high_school_year=request.POST.get("high_school_year", "").strip(),
            college=request.POST.get("college", "").strip(),
            college_year=request.POST.get("college_year", "").strip(),

            company_1=request.POST.get("company_1", "").strip(),
            company_address_1=request.POST.get("company_address_1", "").strip(),
            occupation_1=request.POST.get("occupation_1", "").strip(),
            years_1=request.POST.get("years_1", "").strip(),

            company_2=request.POST.get("company_2", "").strip(),
            company_address_2=request.POST.get("company_address_2", "").strip(),
            occupation_2=request.POST.get("occupation_2", "").strip(),
            years_2=request.POST.get("years_2", "").strip(),

            company_3=request.POST.get("company_3", "").strip(),
            company_address_3=request.POST.get("company_address_3", "").strip(),
            occupation_3=request.POST.get("occupation_3", "").strip(),
            years_3=request.POST.get("years_3", "").strip(),

            reference_name_1=request.POST.get("reference_name_1", "").strip(),
            reference_occupation_1=request.POST.get("reference_occupation_1", "").strip(),
            reference_contact_1=request.POST.get("reference_contact_1", "").strip(),

            reference_name_2=request.POST.get("reference_name_2", "").strip(),
            reference_occupation_2=request.POST.get("reference_occupation_2", "").strip(),
            reference_contact_2=request.POST.get("reference_contact_2", "").strip(),

            reference_name_3=request.POST.get("reference_name_3", "").strip(),
            reference_occupation_3=request.POST.get("reference_occupation_3", "").strip(),
            reference_contact_3=request.POST.get("reference_contact_3", "").strip(),

            position=request.POST.get("position", "").strip(),
            rate=request.POST.get("rate") or Decimal("0.00"),
            date_started=request.POST.get("date_started") or None,
        )

        if request.FILES.get("photo"):
            employee.photo = request.FILES.get("photo")

        if request.FILES.get("resume"):
            employee.resume = request.FILES.get("resume")

        employee.save()

        return redirect("/employees-page/")

    return render(
        request,
        "dashboard/new_employee_page.html"
    )