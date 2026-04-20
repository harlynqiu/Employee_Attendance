from rest_framework import serializers
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id',
            'employee',
            'employee_id',
            'employee_name',
            'date',
            'time_in',
            'time_out',
            'worked_hours',
            'payable_hours',
            'late_minutes',
            'undertime_minutes',
        ]
        read_only_fields = [
            'worked_hours',
            'payable_hours',
            'late_minutes',
            'undertime_minutes',
        ]