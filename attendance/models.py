from decimal import Decimal
from datetime import time, datetime

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from employees.models import Employee


class Attendance(models.Model):

    ATTENDANCE_STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('leave', 'Leave'),
        ('rest_day', 'Rest Day'),
        ('holiday', 'Holiday'),
    )

    WORK_TYPE_CHOICES = (
        ('office', 'Office'),
        ('deliver', 'Deliver'),
        ('booking', 'Booking'),
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendances'
    )

    date = models.DateField(
        default=timezone.localdate
    )

    status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS_CHOICES,
        default='present'
    )

    time_in = models.DateTimeField(
        null=True,
        blank=True
    )

    time_out = models.DateTimeField(
        null=True,
        blank=True
    )

    worked_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    payable_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    late_minutes = models.PositiveIntegerField(
        default=0
    )

    undertime_minutes = models.PositiveIntegerField(
        default=0
    )

    overtime_applicable = models.BooleanField(
        default=False
    )

    overtime_minutes = models.PositiveIntegerField(
        default=0
    )

    transportation_fee_applicable = models.BooleanField(
        default=True
    )

    work_type = models.CharField(
        max_length=20,
        choices=WORK_TYPE_CHOICES,
        default='office'
    )

    delivery_allowance_applicable = models.BooleanField(
        default=False
    )

    work_location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Example: Digos, Kidapawan, Tagum'
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ('employee', 'date')

        ordering = [
            '-date',
            '-time_in'
        ]

    @property
    def time_in_display(self):
        if self.time_in:
            return timezone.localtime(self.time_in).strftime('%I:%M %p')
        return '-'

    @property
    def time_out_display(self):
        if self.time_out:
            return timezone.localtime(self.time_out).strftime('%I:%M %p')
        return '-'

    @property
    def date_display(self):
        if self.date:
            return self.date.strftime('%b %d, %Y')
        return '-'

    @property
    def worked_hours_display(self):
        return self.worked_hours or Decimal('0.00')

    @property
    def payable_hours_display(self):
        return self.payable_hours or Decimal('0.00')

    def clean(self):

        if (
            self.time_in
            and self.time_out
            and self.time_out < self.time_in
        ):
            raise ValidationError({
                'time_out':
                'Time out cannot be earlier than time in.'
            })

        if self.status in [
            'absent',
            'leave',
            'rest_day',
            'holiday'
        ]:
            if self.time_in or self.time_out:
                raise ValidationError({
                    'status':
                    'Absent, Leave, Rest Day, or Holiday should not have time in/time out.'
                })

    def save(self, *args, **kwargs):

        self.full_clean()

        if self.status in [
            'absent',
            'leave',
            'rest_day',
            'holiday'
        ]:

            self.time_in = None
            self.time_out = None

            self.worked_hours = Decimal('0.00')
            self.payable_hours = Decimal('0.00')

            self.late_minutes = 0
            self.undertime_minutes = 0
            self.overtime_minutes = 0

            self.overtime_applicable = False
            self.transportation_fee_applicable = False
            self.delivery_allowance_applicable = False

        elif self.status == 'half_day':

            self.worked_hours = Decimal('4.00')
            self.payable_hours = Decimal('4.00')

            self.late_minutes = 0
            self.undertime_minutes = 0
            self.overtime_minutes = 0

        elif self.time_in and self.time_out:

            local_in = timezone.localtime(self.time_in)
            local_out = timezone.localtime(self.time_out)

            work_date = local_in.date()
            current_timezone = timezone.get_current_timezone()

            official_start = timezone.make_aware(
                datetime.combine(work_date, time(8, 0)),
                current_timezone
            )

            grace_end = timezone.make_aware(
                datetime.combine(work_date, time(8, 5)),
                current_timezone
            )

            official_end = timezone.make_aware(
                datetime.combine(work_date, time(17, 0)),
                current_timezone
            )

            lunch_start = timezone.make_aware(
                datetime.combine(work_date, time(12, 0)),
                current_timezone
            )

            lunch_end = timezone.make_aware(
                datetime.combine(work_date, time(13, 0)),
                current_timezone
            )

            if local_in <= grace_end:
                credited_in = official_start
                self.late_minutes = 0
            else:
                credited_in = local_in
                self.late_minutes = round(
                    (local_in - grace_end).total_seconds() / 60
                )

            if (
                self.overtime_applicable
                and local_out > official_end
            ):
                self.overtime_minutes = round(
                    (local_out - official_end).total_seconds() / 60
                )

                credited_out = official_end

            else:
                self.overtime_minutes = 0

                credited_out = min(
                    local_out,
                    official_end
                )

            if local_out < official_end:
                self.undertime_minutes = round(
                    (official_end - local_out).total_seconds() / 60
                )
            else:
                self.undertime_minutes = 0

            if credited_out > credited_in:
                worked_seconds = (
                    credited_out - credited_in
                ).total_seconds()
            else:
                worked_seconds = 0

            lunch_overlap_start = max(
                credited_in,
                lunch_start
            )

            lunch_overlap_end = min(
                credited_out,
                lunch_end
            )

            lunch_seconds = 0

            if lunch_overlap_end > lunch_overlap_start:
                lunch_seconds = (
                    lunch_overlap_end - lunch_overlap_start
                ).total_seconds()

            payable_seconds = max(
                worked_seconds - lunch_seconds,
                0
            )

            self.worked_hours = Decimal(
                str(round(worked_seconds / 3600, 2))
            )

            self.payable_hours = Decimal(
                str(round(payable_seconds / 3600, 2))
            )

        else:

            self.worked_hours = None
            self.payable_hours = None

            self.late_minutes = 0
            self.undertime_minutes = 0
            self.overtime_minutes = 0

        super().save(*args, **kwargs)

    def __str__(self):

        return (
            f"{self.employee.employee_id}"
            f" - {self.employee.full_name}"
            f" - {self.date}"
        )