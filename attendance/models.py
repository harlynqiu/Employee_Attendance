from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from employees.models import Employee
from datetime import time, datetime


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.localdate)
    time_in = models.DateTimeField(null=True, blank=True)
    time_out = models.DateTimeField(null=True, blank=True)

    worked_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    payable_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    late_minutes = models.PositiveIntegerField(default=0)
    undertime_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date', '-time_in']

    def clean(self):
        if self.time_in and self.time_out and self.time_out < self.time_in:
            raise ValidationError({
                'time_out': 'Time out cannot be earlier than time in.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.time_in and self.time_out:
            local_in = timezone.localtime(self.time_in)
            local_out = timezone.localtime(self.time_out)

            work_date = local_in.date()

            official_start = timezone.make_aware(
                datetime.combine(work_date, time(8, 0))
            )
            grace_end = timezone.make_aware(
                datetime.combine(work_date, time(8, 5))
            )
            official_end = timezone.make_aware(
                datetime.combine(work_date, time(17, 0))
            )
            lunch_start = timezone.make_aware(
                datetime.combine(work_date, time(12, 0))
            )
            lunch_end = timezone.make_aware(
                datetime.combine(work_date, time(13, 0))
            )

            # No extra for early arrivals
            # Grace period counts as if employee arrived exactly at 8:00 AM
            if local_in <= grace_end:
                credited_in = official_start
                self.late_minutes = 0
            else:
                credited_in = local_in
                self.late_minutes = int((local_in - grace_end).total_seconds() // 60)

            # No overtime yet
            credited_out = min(local_out, official_end)

            # Undertime
            if local_out < official_end:
                self.undertime_minutes = int((official_end - local_out).total_seconds() // 60)
            else:
                self.undertime_minutes = 0

            # Compute worked duration
            if credited_out > credited_in:
                worked_seconds = (credited_out - credited_in).total_seconds()
            else:
                worked_seconds = 0

            # Deduct lunch only if the credited time overlaps 12:00 PM to 1:00 PM
            lunch_overlap_start = max(credited_in, lunch_start)
            lunch_overlap_end = min(credited_out, lunch_end)

            lunch_seconds = 0
            if lunch_overlap_end > lunch_overlap_start:
                lunch_seconds = (lunch_overlap_end - lunch_overlap_start).total_seconds()

            payable_seconds = max(worked_seconds - lunch_seconds, 0)

            self.worked_hours = Decimal(str(round(worked_seconds / 3600, 2)))
            self.payable_hours = Decimal(str(round(payable_seconds / 3600, 2)))
        else:
            self.worked_hours = None
            self.payable_hours = None
            self.late_minutes = 0
            self.undertime_minutes = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.employee_id} - {self.employee.full_name} - {self.date}"