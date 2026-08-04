from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

from rest_framework import viewsets

from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().order_by("-id")
    serializer_class = EmployeeSerializer


def _clean_text(request, field_name):
    """
    Return a stripped POST value.

    Empty values are returned as an empty string. This works with model fields
    that allow blank=True and null=True.
    """
    return request.POST.get(field_name, "").strip()


def _clean_date(request, field_name):
    """
    Return the submitted date string or None.

    Django accepts a valid YYYY-MM-DD string when assigning it to a DateField.
    """
    return request.POST.get(field_name) or None


def _clean_decimal(request, field_name, default="0.00"):
    """
    Convert a submitted value to Decimal.

    Invalid or empty values fall back to the supplied default.
    """
    raw_value = request.POST.get(field_name, "").strip()

    if not raw_value:
        return Decimal(default)

    try:
        return Decimal(raw_value)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _assign_employee_fields(employee, request):
    """
    Assign all employee form fields from request.POST.

    The HTML input names must match the names used below.
    """

    # PERSONAL INFORMATION
    employee.first_name = _clean_text(request, "first_name")
    employee.middle_initial = _clean_text(request, "middle_initial")
    employee.last_name = _clean_text(request, "last_name")
    employee.date_of_birth = _clean_date(request, "date_of_birth")
    employee.citizenship = _clean_text(request, "citizenship")
    employee.address = _clean_text(request, "address")
    employee.contact_number = _clean_text(request, "contact_number")
    employee.spouse_name = _clean_text(request, "spouse_name")
    employee.spouse_contact_number = _clean_text(
        request,
        "spouse_contact_number",
    )
    employee.blood_type = _clean_text(request, "blood_type")

    # EMERGENCY INFORMATION
    employee.emergency_contact_name = _clean_text(
        request,
        "emergency_contact_name",
    )
    employee.emergency_relationship = _clean_text(
        request,
        "emergency_relationship",
    )
    employee.emergency_contact_number = _clean_text(
        request,
        "emergency_contact_number",
    )
    employee.emergency_address = _clean_text(
        request,
        "emergency_address",
    )

    # EDUCATIONAL INFORMATION
    employee.elementary = _clean_text(request, "elementary")
    employee.elementary_year = _clean_text(request, "elementary_year")
    employee.high_school = _clean_text(request, "high_school")
    employee.high_school_year = _clean_text(request, "high_school_year")
    employee.college = _clean_text(request, "college")
    employee.college_year = _clean_text(request, "college_year")

    # EMPLOYMENT HISTORY
    employee.company_1 = _clean_text(request, "company_1")
    employee.company_address_1 = _clean_text(
        request,
        "company_address_1",
    )
    employee.occupation_1 = _clean_text(request, "occupation_1")
    employee.years_1 = _clean_text(request, "years_1")

    employee.company_2 = _clean_text(request, "company_2")
    employee.company_address_2 = _clean_text(
        request,
        "company_address_2",
    )
    employee.occupation_2 = _clean_text(request, "occupation_2")
    employee.years_2 = _clean_text(request, "years_2")

    employee.company_3 = _clean_text(request, "company_3")
    employee.company_address_3 = _clean_text(
        request,
        "company_address_3",
    )
    employee.occupation_3 = _clean_text(request, "occupation_3")
    employee.years_3 = _clean_text(request, "years_3")

    # CHARACTER REFERENCES
    employee.reference_name_1 = _clean_text(
        request,
        "reference_name_1",
    )
    employee.reference_occupation_1 = _clean_text(
        request,
        "reference_occupation_1",
    )
    employee.reference_contact_1 = _clean_text(
        request,
        "reference_contact_1",
    )

    employee.reference_name_2 = _clean_text(
        request,
        "reference_name_2",
    )
    employee.reference_occupation_2 = _clean_text(
        request,
        "reference_occupation_2",
    )
    employee.reference_contact_2 = _clean_text(
        request,
        "reference_contact_2",
    )

    employee.reference_name_3 = _clean_text(
        request,
        "reference_name_3",
    )
    employee.reference_occupation_3 = _clean_text(
        request,
        "reference_occupation_3",
    )
    employee.reference_contact_3 = _clean_text(
        request,
        "reference_contact_3",
    )

    # GOVERNMENT INFORMATION
    employee.sss_number = _clean_text(request, "sss_number")
    employee.philhealth_number = _clean_text(
        request,
        "philhealth_number",
    )
    employee.tin_number = _clean_text(request, "tin_number")
    employee.pagibig_number = _clean_text(request, "pagibig_number")
    employee.nbi_clearance_number = _clean_text(
        request,
        "nbi_clearance_number",
    )

    # OPTIONAL GOVERNMENT FIELDS STILL PRESENT IN THE MODEL
    employee.barangay_clearance_number = _clean_text(
        request,
        "barangay_clearance_number",
    )
    employee.drivers_license_number = _clean_text(
        request,
        "drivers_license_number",
    )

    # WORK INFORMATION
    employee.position = _clean_text(request, "position")
    employee.employment_status = (
        request.POST.get("employment_status") or "ACTIVE"
    )
    employee.employment_remarks = _clean_text(
        request,
        "employment_remarks",
    )
    employee.salary_type = request.POST.get("salary_type") or "daily"
    employee.rate = _clean_decimal(request, "rate")
    employee.benefits = _clean_decimal(request, "benefits")
    employee.date_started = _clean_date(request, "date_started")


def _assign_employee_files(employee, request):
    """
    Replace a stored file only when a new file is submitted.

    Existing files remain unchanged when the user leaves an upload input empty.
    """
    file_fields = (
        "photo",
        "resume",
        "sss_file",
        "philhealth_file",
        "tin_file",
        "pagibig_file",
        "nbi_clearance_file",
        "barangay_clearance_file",
        "drivers_license_file",
    )

    for field_name in file_fields:
        uploaded_file = request.FILES.get(field_name)

        if uploaded_file:
            setattr(employee, field_name, uploaded_file)


def employees_page(request):
    status_filter = request.GET.get("status", "ALL")
    q = request.GET.get("q", "").strip()

    employees = Employee.objects.all().order_by("employee_id")

    if status_filter != "ALL":
        employees = employees.filter(
            employment_status=status_filter,
        )

    if q:
        employees = employees.filter(
            Q(employee_id__icontains=q)
            | Q(first_name__icontains=q)
            | Q(middle_initial__icontains=q)
            | Q(last_name__icontains=q)
            | Q(position__icontains=q)
            | Q(contact_number__icontains=q)
        )

    employees = employees.annotate(
        attendance_count=Count(
            "attendances",
            distinct=True,
        ),
        payroll_count=Count(
            "payrolls",
            distinct=True,
        ),
        total_cash_advance=Coalesce(
            Sum("payrolls__cash_advance"),
            Decimal("0.00"),
        ),
        total_charges_amount=Coalesce(
            Sum("payrolls__charges"),
            Decimal("0.00"),
        ),
        total_rent=Coalesce(
            Sum("payrolls__rent"),
            Decimal("0.00"),
        ),
        total_benefits=Coalesce(
            Sum("payrolls__benefits"),
            Decimal("0.00"),
        ),
    )

    total_employees = Employee.objects.count()

    active_employees = Employee.objects.filter(
        employment_status="ACTIVE",
    ).count()

    resigned_employees = Employee.objects.filter(
        employment_status="RESIGNED",
    ).count()

    mia_employees = Employee.objects.filter(
        employment_status="MIA",
    ).count()

    terminated_employees = Employee.objects.filter(
        employment_status="TERMINATED",
    ).count()

    active_rates = Employee.objects.filter(
        employment_status="ACTIVE",
    ).exclude(
        rate__isnull=True,
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
        context,
    )


def view_employee_page_view(request, employee_id):
    employee = get_object_or_404(
        Employee,
        id=employee_id,
    )

    attendances = employee.attendances.all().order_by("-date")[:10]
    payrolls = employee.payrolls.all().order_by("-start_date")[:10]

    total_charges = Decimal("0.00")

    for payroll in employee.payrolls.all():
        total_charges += (
            (payroll.cash_advance or Decimal("0.00"))
            + (payroll.charges or Decimal("0.00"))
            + (payroll.rent or Decimal("0.00"))
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
        context,
    )


def new_employee_page(request):
    if request.method == "POST":
        employee = Employee()

        _assign_employee_fields(employee, request)
        _assign_employee_files(employee, request)

        try:
            employee.save()
        except Exception as error:
            messages.error(
                request,
                f"Employee could not be saved: {error}",
            )

            return render(
                request,
                "dashboard/new_employee_page.html",
                {
                    "submitted_data": request.POST,
                },
            )

        messages.success(
            request,
            f"{employee.full_name} was added successfully.",
        )

        return redirect(
            "view_employee_page",
            employee_id=employee.id,
        )

    return render(
        request,
        "dashboard/new_employee_page.html",
    )


def edit_employee_page(request, employee_id):
    employee = get_object_or_404(
        Employee,
        id=employee_id,
    )

    if request.method == "POST":
        _assign_employee_fields(employee, request)
        _assign_employee_files(employee, request)

        try:
            employee.save()
        except Exception as error:
            messages.error(
                request,
                f"Employee changes could not be saved: {error}",
            )

            return render(
                request,
                "dashboard/edit_employee_page.html",
                {
                    "employee": employee,
                },
            )

        messages.success(
            request,
            f"{employee.full_name}'s record was updated successfully.",
        )

        return redirect(
            "view_employee_page",
            employee_id=employee.id,
        )

    return render(
        request,
        "dashboard/edit_employee_page.html",
        {
            "employee": employee,
        },
    )