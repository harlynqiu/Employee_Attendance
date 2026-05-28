from datetime import timedelta, datetime
from decimal import Decimal

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Q
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from employees.models import Employee
from .models import Attendance
from .serializers import AttendanceSerializer


def get_employee_name(employee):
    return f"{employee.last_name}, {employee.first_name}"


def parse_datetime_value(value):
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        return datetime.fromisoformat(value)

    return None


def calculate_payable_hours(time_in_value, time_out_value):
    datetime_in = parse_datetime_value(time_in_value)
    datetime_out = parse_datetime_value(time_out_value)

    if not datetime_in or not datetime_out:
        return Decimal("0.00")

    total_hours = (datetime_out - datetime_in).total_seconds() / 3600
    return Decimal(str(round(max(total_hours, 0), 2)))


def attendance_page(request):
    q = request.GET.get("q", "").strip()
    today = timezone.localdate()

    attendance_records = Attendance.objects.select_related(
        "employee"
    ).filter(
        date=today
    ).order_by(
        "employee__employee_id"
    )

    if q:
        attendance_records = attendance_records.filter(
            Q(employee__employee_id__icontains=q) |
            Q(employee__first_name__icontains=q) |
            Q(employee__last_name__icontains=q) |
            Q(employee__position__icontains=q)
        )

    past_attendances = Attendance.objects.select_related(
        "employee"
    ).filter(
        date__lt=today
    ).order_by(
        "-date",
        "employee__employee_id"
    )[:20]

    context = {
        "attendance_records": attendance_records,
        "past_attendances": past_attendances,
        "current_date": today,
        "q": q,
    }

    return render(
        request,
        "dashboard/attendance_page.html",
        context
    )


def scanner_page(request):
    return render(request, "scanner.html")


@csrf_exempt
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def scan_attendance(request):
    try:
        employee_id = request.data.get("employee_id")
        scan_type = request.data.get("scan_type")

        if not employee_id:
            return Response(
                {
                    "success": False,
                    "error": "employee_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if scan_type not in ["time_in", "time_out"]:
            return Response(
                {
                    "success": False,
                    "error": "Please select TIME IN or TIME OUT."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        employee = Employee.objects.get(employee_id=employee_id)
        employee_name = get_employee_name(employee)

        today = timezone.localdate()
        now = timezone.localtime()
        now_iso = now.isoformat()
        now_display = now.strftime("%I:%M %p")

        attendance = Attendance.objects.filter(
            employee=employee,
            date=today
        ).first()

        if scan_type == "time_in":
            if attendance and attendance.time_in:
                return Response(
                    {
                        "success": False,
                        "message": "Employee has already timed in today.",
                        "employee_id": employee.employee_id,
                        "employee_name": employee_name,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            Attendance.objects.create(
                employee=employee,
                date=today,
                time_in=now_iso
            )

            return Response(
                {
                    "success": True,
                    "type": "TIME IN",
                    "message": "Time in recorded successfully.",
                    "employee_id": employee.employee_id,
                    "employee_name": employee_name,
                    "time": now_display,
                },
                status=status.HTTP_201_CREATED
            )

        if scan_type == "time_out":
            if not attendance:
                return Response(
                    {
                        "success": False,
                        "message": "No time-in record found for today.",
                        "employee_id": employee.employee_id,
                        "employee_name": employee_name,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if attendance.time_out:
                return Response(
                    {
                        "success": False,
                        "message": "Employee has already timed out today.",
                        "employee_id": employee.employee_id,
                        "employee_name": employee_name,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            attendance.time_out = now_iso
            attendance.payable_hours = calculate_payable_hours(
                attendance.time_in,
                attendance.time_out
            )
            attendance.save()

            return Response(
                {
                    "success": True,
                    "type": "TIME OUT",
                    "message": "Time out recorded successfully.",
                    "employee_id": employee.employee_id,
                    "employee_name": employee_name,
                    "time": now_display,
                    "payable_hours": str(attendance.payable_hours),
                },
                status=status.HTTP_200_OK
            )

    except Employee.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Employee not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {
                "success": False,
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def time_in_view(request):
    employee_id = request.data.get("employee_id")

    if not employee_id:
        return Response(
            {"error": "employee_id is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    today = timezone.localdate()
    now = timezone.localtime()
    now_iso = now.isoformat()

    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        date=today,
        defaults={"time_in": now_iso}
    )

    if not created:
        if attendance.time_in:
            return Response(
                {"error": "Employee has already timed in for today."},
                status=status.HTTP_400_BAD_REQUEST
            )

        attendance.time_in = now_iso
        attendance.save()

    serializer = AttendanceSerializer(attendance)

    return Response(
        {
            "message": "Time in recorded successfully.",
            "attendance": serializer.data
        },
        status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
def time_out_view(request):
    employee_id = request.data.get("employee_id")

    if not employee_id:
        return Response(
            {"error": "employee_id is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    today = timezone.localdate()
    now = timezone.localtime()
    now_iso = now.isoformat()

    try:
        attendance = Attendance.objects.get(
            employee=employee,
            date=today
        )
    except Attendance.DoesNotExist:
        return Response(
            {"error": "No time-in record found for today."},
            status=status.HTTP_404_NOT_FOUND
        )

    if not attendance.time_in:
        return Response(
            {"error": "Employee has not timed in yet."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if attendance.time_out:
        return Response(
            {"error": "Employee has already timed out for today."},
            status=status.HTTP_400_BAD_REQUEST
        )

    attendance.time_out = now_iso
    attendance.payable_hours = calculate_payable_hours(
        attendance.time_in,
        attendance.time_out
    )
    attendance.save()

    serializer = AttendanceSerializer(attendance)

    return Response(
        {
            "message": "Time out recorded successfully.",
            "attendance": serializer.data
        },
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
def attendance_list_view(request):
    attendance = Attendance.objects.select_related(
        "employee"
    ).all().order_by(
        "-date",
        "-time_in"
    )

    serializer = AttendanceSerializer(attendance, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def employee_attendance_view(request, employee_id):
    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    attendance = Attendance.objects.filter(
        employee=employee
    ).order_by(
        "-date",
        "-time_in"
    )

    serializer = AttendanceSerializer(attendance, many=True)

    return Response({
        "employee_id": employee.employee_id,
        "employee_name": get_employee_name(employee),
        "attendance": serializer.data
    })


@api_view(["GET"])
def employee_weekly_attendance_view(request, employee_id):
    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    today = timezone.localdate()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    attendance = Attendance.objects.filter(
        employee=employee,
        date__range=[start_of_week, end_of_week]
    ).order_by(
        "date",
        "time_in"
    )

    serializer = AttendanceSerializer(attendance, many=True)

    return Response({
        "employee_id": employee.employee_id,
        "employee_name": get_employee_name(employee),
        "week_start": start_of_week,
        "week_end": end_of_week,
        "attendance": serializer.data
    })


@api_view(["GET"])
def employee_monthly_attendance_view(request, employee_id):
    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    today = timezone.localdate()

    attendance = Attendance.objects.filter(
        employee=employee,
        date__year=today.year,
        date__month=today.month
    ).order_by(
        "date",
        "time_in"
    )

    serializer = AttendanceSerializer(attendance, many=True)

    return Response({
        "employee_id": employee.employee_id,
        "employee_name": get_employee_name(employee),
        "month": today.month,
        "year": today.year,
        "attendance": serializer.data
    })


@api_view(["GET"])
def employee_attendance_by_month_view(request, employee_id):
    year = request.GET.get("year")
    month = request.GET.get("month")

    if not year or not month:
        return Response(
            {"error": "year and month are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        year = int(year)
        month = int(month)
        employee = Employee.objects.get(employee_id=employee_id)
    except ValueError:
        return Response(
            {"error": "year and month must be integers."},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    attendance = Attendance.objects.filter(
        employee=employee,
        date__year=year,
        date__month=month
    ).order_by("date")

    serializer = AttendanceSerializer(attendance, many=True)

    return Response({
        "employee_id": employee.employee_id,
        "employee_name": get_employee_name(employee),
        "year": year,
        "month": month,
        "attendance": serializer.data
    })


@api_view(["GET"])
def employee_attendance_by_range_view(request, employee_id):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date or not end_date:
        return Response(
            {"error": "start_date and end_date are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    attendance = Attendance.objects.filter(
        employee=employee,
        date__range=[start_date, end_date]
    ).order_by("date")

    serializer = AttendanceSerializer(attendance, many=True)

    return Response({
        "employee_id": employee.employee_id,
        "employee_name": get_employee_name(employee),
        "start_date": start_date,
        "end_date": end_date,
        "attendance": serializer.data
    })


def build_summary(attendance_qs):
    days_present = attendance_qs.filter(
        time_in__isnull=False
    ).count()

    total_late_minutes = attendance_qs.aggregate(
        total=Sum("late_minutes")
    )["total"] or 0

    total_undertime_minutes = attendance_qs.aggregate(
        total=Sum("undertime_minutes")
    )["total"] or 0

    total_payable_hours = attendance_qs.aggregate(
        total=Sum("payable_hours")
    )["total"] or 0

    return {
        "days_present": days_present,
        "total_late_minutes": total_late_minutes,
        "total_undertime_minutes": total_undertime_minutes,
        "total_payable_hours": total_payable_hours,
    }


@api_view(["GET"])
def employee_summary_by_month_view(request, employee_id):
    year = request.GET.get("year")
    month = request.GET.get("month")

    if not year or not month:
        return Response(
            {"error": "year and month are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        year = int(year)
        month = int(month)
        employee = Employee.objects.get(employee_id=employee_id)
    except ValueError:
        return Response(
            {"error": "year and month must be integers."},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    attendance = Attendance.objects.filter(
        employee=employee,
        date__year=year,
        date__month=month
    )

    summary = build_summary(attendance)

    return Response({
        "employee_id": employee.employee_id,
        "employee_name": get_employee_name(employee),
        "year": year,
        "month": month,
        "summary": summary
    })


@api_view(["GET"])
def employee_summary_by_range_view(request, employee_id):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date or not end_date:
        return Response(
            {"error": "start_date and end_date are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    attendance = Attendance.objects.filter(
        employee=employee,
        date__range=[start_date, end_date]
    )

    summary = build_summary(attendance)

    return Response({
        "employee_id": employee.employee_id,
        "employee_name": get_employee_name(employee),
        "start_date": start_date,
        "end_date": end_date,
        "summary": summary
    })