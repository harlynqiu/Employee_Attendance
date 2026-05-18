from django import forms
from django.utils import timezone

from employees.models import Employee


class AttendanceBulkEntryForm(forms.Form):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('leave', 'Leave'),
        ('rest_day', 'Rest Day'),
        ('holiday', 'Holiday'),
    ]

    date = forms.DateField(
        label='Date',
        initial=timezone.localdate,
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CHOICES,
        initial='present',
        required=True
    )

    time_in = forms.TimeField(
        label='Time in',
        required=False,
        input_formats=['%I:%M %p', '%I:%M%p', '%H:%M', '%H:%M:%S'],
        initial='8:00 AM',
        widget=forms.TextInput(attrs={'placeholder': '8:00 AM'})
    )

    time_out = forms.TimeField(
        label='Time out',
        required=False,
        input_formats=['%I:%M %p', '%I:%M%p', '%H:%M', '%H:%M:%S'],
        initial='5:00 PM',
        widget=forms.TextInput(attrs={'placeholder': '5:00 PM'})
    )

    overtime_applicable = forms.BooleanField(
        label='Overtime applicable',
        required=False,
        initial=False
    )

    transportation_fee_applicable = forms.BooleanField(
        label='Transportation fee applicable',
        required=False,
        initial=True
    )

    employees = forms.ModelMultipleChoiceField(
        label='Employees',
        queryset=Employee.objects.all().order_by('last_name', 'first_name'),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get('status')
        time_in = cleaned_data.get('time_in')
        time_out = cleaned_data.get('time_out')

        if status in ['present', 'half_day']:
            if not time_in:
                self.add_error('time_in', 'Time in is required.')
            if not time_out:
                self.add_error('time_out', 'Time out is required.')

        return cleaned_data