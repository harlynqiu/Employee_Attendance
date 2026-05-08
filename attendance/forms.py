from datetime import datetime

from django import forms
from django.utils import timezone

from .models import Attendance


class AttendanceAdminForm(forms.ModelForm):
    time_in_time = forms.TimeField(
        required=False,
        label='Time in',
        input_formats=['%I:%M %p', '%I:%M%p', '%H:%M', '%H:%M:%S'],
        widget=forms.TextInput(attrs={'placeholder': '8:00 AM'})
    )

    time_out_time = forms.TimeField(
        required=False,
        label='Time out',
        input_formats=['%I:%M %p', '%I:%M%p', '%H:%M', '%H:%M:%S'],
        widget=forms.TextInput(attrs={'placeholder': '5:00 PM'})
    )

    class Meta:
        model = Attendance
        fields = (
            'employee',
            'date',
            'status',
            'time_in_time',
            'time_out_time',
            'overtime_applicable',
            'transportation_fee_applicable',
            'work_type',
            'delivery_allowance_applicable',
            'work_location',
            'remarks',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['time_in_time'].initial = (
                timezone.localtime(self.instance.time_in).strftime('%I:%M %p')
                if self.instance.time_in else '8:00 AM'
            )
            self.fields['time_out_time'].initial = (
                timezone.localtime(self.instance.time_out).strftime('%I:%M %p')
                if self.instance.time_out else '5:00 PM'
            )
        else:
            self.fields['time_in_time'].initial = '8:00 AM'
            self.fields['time_out_time'].initial = '5:00 PM'

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get('status')
        time_in_time = cleaned_data.get('time_in_time')
        time_out_time = cleaned_data.get('time_out_time')
        work_type = cleaned_data.get('work_type')
        delivery_allowance_applicable = cleaned_data.get('delivery_allowance_applicable')

        if status in ['present', 'half_day']:
            if not time_in_time:
                self.add_error('time_in_time', 'Time in is required.')
            if not time_out_time:
                self.add_error('time_out_time', 'Time out is required.')

        if delivery_allowance_applicable and work_type != 'deliver':
            self.add_error(
                'delivery_allowance_applicable',
                'Delivery allowance can only be applied when Work Type is Deliver.'
            )

        return cleaned_data

    def save(self, commit=True):
        attendance = super().save(commit=False)

        attendance_date = self.cleaned_data.get('date')
        status = self.cleaned_data.get('status')
        time_in_time = self.cleaned_data.get('time_in_time')
        time_out_time = self.cleaned_data.get('time_out_time')
        work_type = self.cleaned_data.get('work_type')

        if status in ['absent', 'leave', 'rest_day', 'holiday']:
            attendance.time_in = None
            attendance.time_out = None
            attendance.overtime_applicable = False
            attendance.transportation_fee_applicable = False
            attendance.delivery_allowance_applicable = False

        else:
            if attendance_date and time_in_time:
                attendance.time_in = timezone.make_aware(
                    datetime.combine(attendance_date, time_in_time)
                )

            if attendance_date and time_out_time:
                attendance.time_out = timezone.make_aware(
                    datetime.combine(attendance_date, time_out_time)
                )

            if work_type != 'deliver':
                attendance.delivery_allowance_applicable = False

        if commit:
            attendance.save()

        return attendance