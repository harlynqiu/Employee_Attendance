from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from employees.models import Employee
from .models import Attendance
from .serializers import AttendanceSerializer


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
    now = timezone.now()

    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        date=today,
        defaults={'time_in': now}
    )

    if not created:
        if attendance.time_in:
            return Response(
                {'error': 'Employee has already timed in for today.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        attendance.time_in = now
        attendance.save()

    serializer = AttendanceSerializer(attendance)
    return Response(
        {
            'message': 'Time in recorded successfully.',
            'attendance': serializer.data
        },
        status=status.HTTP_201_CREATED
    )


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
    now = timezone.now()

    try:
        attendance = Attendance.objects.get(employee=employee, date=today)
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

    attendance.time_out = now
    attendance.save()

    serializer = AttendanceSerializer(attendance)
    return Response(
        {
            'message': 'Time out recorded successfully.',
            'attendance': serializer.data
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
def attendance_list_view(request):
    attendance = Attendance.objects.select_related('employee').all()
    serializer = AttendanceSerializer(attendance, many=True)
    return Response(serializer.data)