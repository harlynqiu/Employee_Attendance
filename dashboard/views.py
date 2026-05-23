from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from employees.models import Employee
from attendance.models import Attendance


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
        'employee__employee_id'
    )

    context = {
        'current_date': now.strftime("%B %d, %Y"),
        'attendance_records': attendance_records,
    }

    return render(request, 'dashboard/attendance_page.html', context)


# BELOW IS FOR THE EMPLOYEES #---------------------

def employees_page_view(request):
    employees = Employee.objects.all().order_by('employee_id')

    context = {
        'employees': employees,
    }

    return render(request, 'dashboard/employees_page.html', context)


# BELOW IS FOR THE ADDING NEW EMPLOYEES #---------------------

def new_employee_page_view(request):
    return render(request, 'dashboard/new_employee_page.html')


# BELOW IS FOR VIEWING EMPLOYEE PROFILE #---------------------

def view_employee_page_view(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    context = {
        'employee': employee,
    }

    return render(request, 'dashboard/view_employee_page.html', context)


# BELOW IS FOR EDITING EMPLOYEE INFORMATION #---------------------

def edit_employee_page_view(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        print("FILES:", request.FILES)

        employee.first_name = request.POST.get('first_name', '')
        employee.middle_initial = request.POST.get('middle_initial', '')
        employee.last_name = request.POST.get('last_name', '')

        employee.address = request.POST.get('address', '')
        employee.contact_number = request.POST.get('contact_number', '')

        employee.spouse_name = request.POST.get('spouse_name', '')
        employee.spouse_contact_number = request.POST.get('spouse_contact_number', '')
        employee.citizenship = request.POST.get('citizenship', '')

        employee.date_of_birth = request.POST.get('date_of_birth') or None
        employee.position = request.POST.get('position', '')
        employee.rate = request.POST.get('rate') or 0
        employee.date_started = request.POST.get('date_started') or None

        employee.elementary = request.POST.get('elementary', '')
        employee.high_school = request.POST.get('high_school', '')
        employee.college = request.POST.get('college', '')

        employee.company_1 = request.POST.get('company_1', '')
        employee.company_address_1 = request.POST.get('company_address_1', '')
        employee.occupation_1 = request.POST.get('occupation_1', '')
        employee.years_1 = request.POST.get('years_1', '')

        employee.reference_name_1 = request.POST.get('reference_name_1', '')
        employee.reference_occupation_1 = request.POST.get('reference_occupation_1', '')
        employee.reference_contact_1 = request.POST.get('reference_contact_1', '')

        if 'photo' in request.FILES:
            employee.photo = request.FILES['photo']

        employee.sss_number = request.POST.get('sss_number', '')
        employee.philhealth_number = request.POST.get('philhealth_number', '')
        employee.nbi_clearance_number = request.POST.get('nbi_clearance_number', '')

        if 'sss_file' in request.FILES:
            employee.sss_file = request.FILES['sss_file']

        if 'philhealth_file' in request.FILES:
            employee.philhealth_file = request.FILES['philhealth_file']

        if 'nbi_clearance_file' in request.FILES:
            employee.nbi_clearance_file = request.FILES['nbi_clearance_file']

        employee.save()

        print("SAVED PHOTO:", employee.photo)

        return redirect(f'/employees-page/{employee.id}/')

    return render(request, 'dashboard/edit_employee_page.html', {
        'employee': employee,
    })