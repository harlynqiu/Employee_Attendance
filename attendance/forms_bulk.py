from django import forms
from django.utils import timezone

from employees.models import Employee
from .models import Attendance


class AttendanceBulkEntryForm(forms.Form):
    date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    time_in = forms.TimeField(
        input_formats=['%I:%M %p', '%I:%M%p', '%H:%M', '%H:%M:%S'],
        initial='8:00 AM',
        widget=forms.TextInput(attrs={
            'placeholder': '8:00 AM'
        })
    )

    time_out = forms.TimeField(
        input_formats=['%I:%M %p', '%I:%M%p', '%H:%M', '%H:%M:%S'],
        initial='5:00 PM',
        widget=forms.TextInput(attrs={
            'placeholder': '5:00 PM'
        })
    )

    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.all().order_by('employee_id'),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    transportation_fee_applicable = forms.BooleanField(
        required=False,
        initial=True,
        label='Transportation fee applicable for selected employees'
    )

    work_type = forms.ChoiceField(
        choices=Attendance.WORK_TYPE_CHOICES,
        initial='office',
        required=True
    )

    work_location = forms.CharField(
        required=False,
        max_length=100,
        label='Location / Area',
        widget=forms.TextInput(attrs={
            'placeholder': 'Example: Digos, Kidapawan, Tagum'
        })
    )

    remarks = forms.CharField(
        required=False,
        label='Remarks',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Example: Digos Booking, Kidapawan Deliver'
        })
    )