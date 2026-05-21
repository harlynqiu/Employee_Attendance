from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from employees.models import Employee
from attendance.models import Attendance
from employees.models import Employee

def dashboard_view(request):

    now = timezone.localtime()

    today = now.date()

    current_hour = now.hour

    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%B %d, %Y")

    if 5 <= current_hour < 12:
        greeting = "Good Morning"

    elif 12 <= current_hour < 17:
        greeting = "Good Afternoon"

    else:
        greeting = "Good Evening"

    total_employees = Employee.objects.count()

    checked_in = Attendance.objects.filter(
        date=today,
        time_in__isnull=False
    ).count()

    late = Attendance.objects.filter(
        date=today,
        late_minutes__gt=0
    ).count()

    employees_with_attendance_today = Attendance.objects.filter(
        date=today
    ).values('employee').distinct().count()

    no_attendance = total_employees - employees_with_attendance_today

    context = {
        'greeting': greeting,
        'checked_in': checked_in,
        'no_attendance': no_attendance,
        'late': late,
        'current_time': current_time,
        'current_date': current_date,
    }

    return render(request, 'dashboard/dashboard.html', context)

# BELOW IS FOR THE ATTENDANCE #---------------------

def attendance_page_view(request):
    now = timezone.localtime()
    today = now.date()

    attendance_records = Attendance.objects.filter(
        date=today
    ).select_related('employee').order_by(
        'employee__last_name',
        'employee__first_name'
    )

    context = {
        'current_date': now.strftime("%B %d, %Y"),
        'attendance_records': attendance_records,
    }

    return render(request, 'dashboard/attendance_page.html', context)

# BELOW IS FOR THE EMPLOYEES #---------------------

def employees_page_view(request):
    employees = Employee.objects.all().order_by(
        'last_name',
        'first_name'
    )

    context = {
        'employees': employees,
    }

    return render(request, 'dashboard/employees_page.html', context)

# BELOW IS FOR THE ADDING NEW EMPLOYEES #---------------------

def new_employee_page_view(request):
    return render(request, 'dashboard/new_employee_page.html')

def view_employee_page_view(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    context = {
        'employee': employee,
    }

    return render(request, 'dashboard/view_employee_page.html', context)