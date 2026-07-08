from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from decimal import Decimal

from .models import Payroll
from employees.models import Employee
from attendance.models import Attendance
from django.db import transaction

# =========================================
# PAYROLL DASHBOARD PAGE
# =========================================

def payroll_page(request):

    q = request.GET.get("q", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    payrolls = Payroll.objects.select_related(
        "employee"
    ).filter(
        employee__employment_status="ACTIVE"
    )

    # SEARCH
    if q:
        payrolls = payrolls.filter(
            Q(employee__employee_id__icontains=q) |
            Q(employee__first_name__icontains=q) |
            Q(employee__last_name__icontains=q) |
            Q(employee__position__icontains=q)
        )

    # FILTER START DATE
    if start_date:
        payrolls = payrolls.filter(
            start_date__gte=start_date
        )

    # FILTER END DATE
    if end_date:
        payrolls = payrolls.filter(
            end_date__lte=end_date
        )

    payrolls = payrolls.order_by(
        "employee__employee_id"
    )

    total_deductions = (
        (payrolls.aggregate(total=Sum("cash_advance"))["total"] or 0)
        +
        (payrolls.aggregate(total=Sum("charges"))["total"] or 0)
        +
        (payrolls.aggregate(total=Sum("rent"))["total"] or 0)
        +
        (payrolls.aggregate(total=Sum("benefits"))["total"] or 0)
    )

    context = {
        "payroll_data": payrolls,

        "total_employees": payrolls.values(
            "employee"
        ).distinct().count(),

        "total_payroll": payrolls.aggregate(
            total=Sum("total_salary")
        )["total"] or 0,

        "total_overtime": payrolls.aggregate(
            total=Sum("overtime_pay")
        )["total"] or 0,

        "total_deductions": total_deductions,

        "q": q,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(
        request,
        "admin/payroll/payroll_page.html",
        context
    )

def generate_payroll(request):

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date or not end_date:

        messages.error(
            request,
            "Please select Start Date and End Date."
        )

        return redirect("payroll-page")

    employees = Employee.objects.filter(
        employment_status="ACTIVE"
    )

    created_count = 0

    with transaction.atomic():

        for employee in employees:

            exists = Payroll.objects.filter(
                employee=employee,
                start_date=start_date,
                end_date=end_date
            ).exists()

            if exists:
                continue

            attendance_exists = Attendance.objects.filter(
                employee=employee,
                date__range=[start_date, end_date]
            ).exists()

            if not attendance_exists:
                continue

            Payroll.objects.create(
                employee=employee,
                start_date=start_date,
                end_date=end_date
            )

            created_count += 1

    messages.success(
        request,
        f"{created_count} payroll records generated successfully."
    )

    return redirect(
        f"/payroll-page/?start_date={start_date}&end_date={end_date}"
    )

# =========================================
# ADD PAYROLL PAGE
# =========================================

def add_payroll(request):

    employees = Employee.objects.filter(
        employment_status="ACTIVE"
    ).order_by(
        "employee_id"
    )

    if request.method == "POST":

        employee = get_object_or_404(
            Employee,
            id=request.POST.get("employee"),
            employment_status="ACTIVE"
        )

        Payroll.objects.create(
            employee=employee,

            start_date=request.POST.get(
                "start_date"
            ),

            end_date=request.POST.get(
                "end_date"
            ),

            allowance=request.POST.get(
                "allowance"
            ) or 0,

            cash_advance=request.POST.get(
                "cash_advance"
            ) or 0,

            charges=request.POST.get(
                "charges"
            ) or 0,

            rent=request.POST.get(
                "rent"
            ) or 0,

            remarks=request.POST.get(
                "remarks"
            ),
        )

        messages.success(
            request,
            "Payroll added successfully."
        )

        return redirect(
            "payroll-page"
        )

    return render(
        request,
        "admin/payroll/add_payroll.html",
        {
            "employees": employees,
        }
    )


# =========================================
# VIEW PAYROLL PAGE
# =========================================

def view_payroll(request, payroll_id):

    payroll = get_object_or_404(
        Payroll,
        id=payroll_id
    )

    attendance_records = Attendance.objects.filter(
        employee=payroll.employee,
        date__range=[
            payroll.start_date,
            payroll.end_date
        ]
    ).order_by(
        "date",
        "time_in"
    )

    context = {
        "payroll": payroll,
        "attendance_records": attendance_records,
    }

    return render(
        request,
        "admin/payroll/view_payroll.html",
        context
    )

# =========================================
# EDIT PAYROLL PAGE
# =========================================

def edit_payroll(request, payroll_id):
    payroll = get_object_or_404(Payroll, id=payroll_id)

    attendance_records = Attendance.objects.filter(
        employee=payroll.employee,
        date__range=[payroll.start_date, payroll.end_date]
    ).order_by("date")

    work_type_choices = Attendance._meta.get_field("work_type").choices

    if request.method == "POST":

        for record in attendance_records:
            record.transportation_fee_applicable = (
                request.POST.get(f"transportation_fee_applicable_{record.id}") == "on"
            )

            record.delivery_allowance_applicable = (
                request.POST.get(f"delivery_allowance_applicable_{record.id}") == "on"
            )

            record.work_type = request.POST.get(
                f"work_type_{record.id}",
                record.work_type
            )

            record.work_location = request.POST.get(
                f"work_location_{record.id}",
                ""
            )

            record.remarks = request.POST.get(
                f"attendance_remarks_{record.id}",
                ""
            )

            record.save()

        payroll.allowance = Decimal(request.POST.get("allowance") or 0)
        payroll.cash_advance = Decimal(request.POST.get("cash_advance") or 0)
        payroll.charges = Decimal(request.POST.get("charges") or 0)
        payroll.rent = Decimal(request.POST.get("rent") or 0)
        payroll.remarks = request.POST.get("remarks", "")
        payroll.benefits = Decimal(request.POST.get("benefits") or 0)
        
        payroll.save()

        return redirect("view-payroll", payroll.id)

    return render(request, "admin/payroll/edit_payroll.html", {
        "payroll": payroll,
        "attendance_records": attendance_records,
        "work_type_choices": work_type_choices,
    })