from datetime import timedelta, datetime
from decimal import Decimal

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from employees.models import Employee
from .models import Attendance
from .serializers import AttendanceSerializer


# =========================================================
# SCANNER PAGE
# =========================================================

def scanner_page(request):
    return render(request, 'scanner.html')


# =========================================================
# QR SCANNER ATTENDANCE API
# =========================================================

@api_view(['POST'])
def scan_attendance(request):
    employee_id = request.data.get('employee_id')

    if not employee_id:
        return Response(
            {'error': 'employee_id is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    today = timezone.localdate()
    now = timezone.localtime()

    attendance = Attendance.objects.filter(
        employee=employee,
        date=today
    ).first()

    if not attendance:
        Attendance.objects.create(
            employee=employee,
            date=today,
            time_in=now.time()
        )

        return Response(
            {
                'success': True,
                'type': 'TIME IN',
                'message': 'Time in recorded successfully.',
                'employee_id': employee.employee_id,
                'employee_name': employee.full_name,
                'time': now.strftime('%I:%M %p'),
            },
            status=status.HTTP_201_CREATED
        )

    if attendance and not attendance.time_out:
        attendance.time_out = now.time()

        if attendance.time_in:
            datetime_in = datetime.combine(
                today,
                attendance.time_in
            )

            datetime_out = datetime.combine(
                today,
                attendance.time_out
            )

            total_hours = (
                datetime_out - datetime_in
            ).total_seconds() / 3600

            attendance.payable_hours = Decimal(
                str(round(max(total_hours, 0), 2))
            )

        attendance.save()

        return Response(
            {
                'success': True,
                'type': 'TIME OUT',
                'message': 'Time out recorded successfully.',
                'employee_id': employee.employee_id,
                'employee_name': employee.full_name,
                'time': now.strftime('%I:%M %p'),
                'payable_hours': attendance.payable_hours,
            },
            status=status.HTTP_200_OK
        )

    return Response(
        {
            'success': False,
            'message': 'Employee already timed out today.',
            'employee_id': employee.employee_id,
            'employee_name': employee.full_name,
        },
        status=status.HTTP_400_BAD_REQUEST
    )


# =========================================================
# MANUAL TIME IN
# =========================================================

@api_view(['POST'])
def time_in_view(request):
    employee_id = request.data.get('employee_id')

    if not employee_id:
        return Response(
            {'error': 'employee_id is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    today = timezone.localdate()
    now = timezone.localtime()

    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        date=today,
        defaults={'time_in': now.time()}
    )

    if not created:
        if attendance.time_in:
            return Response(
                {'error': 'Employee has already timed in for today.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attendance.time_in = now.time()
        attendance.save()

    serializer = AttendanceSerializer(attendance)

    return Response(
        {
            'message': 'Time in recorded successfully.',
            'attendance': serializer.data
        },
        status=status.HTTP_201_CREATED
    )


# =========================================================
# MANUAL TIME OUT
# =========================================================

@api_view(['POST'])
def time_out_view(request):
    employee_id = request.data.get('employee_id')

    if not employee_id:
        return Response(
            {'error': 'employee_id is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    today = timezone.localdate()
    now = timezone.localtime()

    try:
        attendance = Attendance.objects.get(
            employee=employee,
            date=today
        )
    except Attendance.DoesNotExist:
        return Response(
            {'error': 'No time-in record found for today.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not attendance.time_in:
        return Response(
            {'error': 'Employee has not timed in yet.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if attendance.time_out:
        return Response(
            {'error': 'Employee has already timed out for today.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    attendance.time_out = now.time()

    datetime_in = datetime.combine(
        today,
        attendance.time_in
    )

    datetime_out = datetime.combine(
        today,
        attendance.time_out
    )

    total_hours = (
        datetime_out - datetime_in
    ).total_seconds() / 3600

    attendance.payable_hours = Decimal(
        str(round(max(total_hours, 0), 2))
    )

    attendance.save()

    serializer = AttendanceSerializer(attendance)

    return Response(
        {
            'message': 'Time out recorded successfully.',
            'attendance': serializer.data
        },
        status=status.HTTP_200_OK
    )


# =========================================================
# ATTENDANCE LIST
# =========================================================

@api_view(['GET'])
def attendance_list_view(request):
    attendance = Attendance.objects.select_related(
        'employee'
    ).all().order_by(
        '-date',
        '-time_in'
    )

    serializer = AttendanceSerializer(
        attendance,
        many=True
    )

    return Response(serializer.data)


# =========================================================
# EMPLOYEE ATTENDANCE
# =========================================================

@api_view(['GET'])
def employee_attendance_view(request, employee_id):
    try:
        employee = Employee.objects.get(
            employee_id=employee_id
        )
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    attendance = Attendance.objects.filter(
        employee=employee
    ).order_by(
        '-date',
        '-time_in'
    )

    serializer = AttendanceSerializer(
        attendance,
        many=True
    )

    return Response({
        'employee_id': employee.employee_id,
        'employee_name': employee.full_name,
        'attendance': serializer.data
    })


@api_view(['GET'])
def employee_weekly_attendance_view(request, employee_id):
    try:
        employee = Employee.objects.get(
            employee_id=employee_id
        )
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    today = timezone.localdate()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    attendance = Attendance.objects.filter(
        employee=employee,
        date__range=[start_of_week, end_of_week]
    ).order_by(
        'date',
        'time_in'
    )

    serializer = AttendanceSerializer(
        attendance,
        many=True
    )

    return Response({
        'employee_id': employee.employee_id,
        'employee_name': employee.full_name,
        'week_start': start_of_week,
        'week_end': end_of_week,
        'attendance': serializer.data
    })


@api_view(['GET'])
def employee_monthly_attendance_view(request, employee_id):
    try:
        employee = Employee.objects.get(
            employee_id=employee_id
        )
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    today = timezone.localdate()

    attendance = Attendance.objects.filter(
        employee=employee,
        date__year=today.year,
        date__month=today.month
    ).order_by(
        'date',
        'time_in'
    )

    serializer = AttendanceSerializer(
        attendance,
        many=True
    )

    return Response({
        'employee_id': employee.employee_id,
        'employee_name': employee.full_name,
        'month': today.month,
        'year': today.year,
        'attendance': serializer.data
    })


@api_view(['GET'])
def employee_attendance_by_month_view(request, employee_id):
    year = request.GET.get('year')
    month = request.GET.get('month')

    if not year or not month:
        return Response(
            {'error': 'year and month are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        return Response(
            {'error': 'year and month must be integers.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(
            employee_id=employee_id
        )
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    attendance = Attendance.objects.filter(
        employee=employee,
        date__year=year,
        date__month=month
    ).order_by('date')

    serializer = AttendanceSerializer(
        attendance,
        many=True
    )

    return Response({
        'employee_id': employee.employee_id,
        'employee_name': employee.full_name,
        'year': year,
        'month': month,
        'attendance': serializer.data
    })


@api_view(['GET'])
def employee_attendance_by_range_view(request, employee_id):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        return Response(
            {'error': 'start_date and end_date are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(
            employee_id=employee_id
        )
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    attendance = Attendance.objects.filter(
        employee=employee,
        date__range=[start_date, end_date]
    ).order_by('date')

    serializer = AttendanceSerializer(
        attendance,
        many=True
    )

    return Response({
        'employee_id': employee.employee_id,
        'employee_name': employee.full_name,
        'start_date': start_date,
        'end_date': end_date,
        'attendance': serializer.data
    })


# =========================================================
# SUMMARY
# =========================================================

def build_summary(attendance_qs):
    days_present = attendance_qs.filter(
        time_in__isnull=False
    ).count()

    total_late_minutes = attendance_qs.aggregate(
        total=Sum('late_minutes')
    )['total'] or 0

    total_undertime_minutes = attendance_qs.aggregate(
        total=Sum('undertime_minutes')
    )['total'] or 0

    total_payable_hours = attendance_qs.aggregate(
        total=Sum('payable_hours')
    )['total'] or 0

    return {
        'days_present': days_present,
        'total_late_minutes': total_late_minutes,
        'total_undertime_minutes': total_undertime_minutes,
        'total_payable_hours': total_payable_hours,
    }


@api_view(['GET'])
def employee_summary_by_month_view(request, employee_id):
    year = request.GET.get('year')
    month = request.GET.get('month')

    if not year or not month:
        return Response(
            {'error': 'year and month are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        return Response(
            {'error': 'year and month must be integers.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(
            employee_id=employee_id
        )
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    attendance = Attendance.objects.filter(
        employee=employee,
        date__year=year,
        date__month=month
    )

    summary = build_summary(attendance)

    return Response({
        'employee_id': employee.employee_id,
        'employee_name': employee.full_name,
        'year': year,
        'month': month,
        'summary': summary
    })


@api_view(['GET'])
def employee_summary_by_range_view(request, employee_id):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        return Response(
            {'error': 'start_date and end_date are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(
            employee_id=employee_id
        )
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    attendance = Attendance.objects.filter(
        employee=employee,
        date__range=[start_date, end_date]
    )

    summary = build_summary(attendance)

    return Response({
        'employee_id': employee.employee_id,
        'employee_name': employee.full_name,
        'start_date': start_date,
        'end_date': end_date,
        'summary': summary
    })