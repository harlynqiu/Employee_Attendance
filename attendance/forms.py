from datetime import datetime

from django import forms
from django.utils import timezone

from .models import Attendance


class AttendanceAdminForm(forms.ModelForm):
    time_in_time = forms.TimeField(
        required=False,
        label='Time in',
        input_formats=['%I:%M %p', '%I:%M%p', '%H:%M', '%H:%M:%S'],
        widget=forms.TextInput(attrs={
            'placeholder': '8:00 AM'
        })
    )

    time_out_time = forms.TimeField(
        required=False,
        label='Time out',
        input_formats=['%I:%M %p', '%I:%M%p', '%H:%M', '%H:%M:%S'],
        widget=forms.TextInput(attrs={
            'placeholder': '5:00 PM'
        })
    )

    class Meta:
        model = Attendance
        fields = (
            'employee',
            'date',
            'status',
            'time_in_time',
            'time_out_time',
            'transportation_fee_applicable',
            'work_type',
            'work_location',
            'remarks',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            if self.instance.time_in:
                self.fields['time_in_time'].initial = timezone.localtime(
                    self.instance.time_in
                ).strftime('%I:%M %p')
            else:
                self.fields['time_in_time'].initial = '8:00 AM'

            if self.instance.time_out:
                self.fields['time_out_time'].initial = timezone.localtime(
                    self.instance.time_out
                ).strftime('%I:%M %p')
            else:
                self.fields['time_out_time'].initial = '5:00 PM'
        else:
            self.fields['time_in_time'].initial = '8:00 AM'
            self.fields['time_out_time'].initial = '5:00 PM'

    def save(self, commit=True):
        attendance = super().save(commit=False)

        attendance_date = self.cleaned_data.get('date')
        status = self.cleaned_data.get('status')
        time_in_time = self.cleaned_data.get('time_in_time')
        time_out_time = self.cleaned_data.get('time_out_time')

        if status in ['absent', 'leave', 'rest_day', 'holiday']:
            attendance.time_in = None
            attendance.time_out = None
        else:
            if attendance_date and time_in_time:
                attendance.time_in = timezone.make_aware(
                    datetime.combine(attendance_date, time_in_time)
                )

            if attendance_date and time_out_time:
                attendance.time_out = timezone.make_aware(
                    datetime.combine(attendance_date, time_out_time)
                )

        if commit:
            attendance.save()

        return attendance