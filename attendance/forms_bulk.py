from django import forms
from django.utils import timezone

from employees.models import Employee


class AttendanceBulkEntryForm(forms.Form):
    date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    time_in = forms.TimeField(
        input_formats=['%I:%M %p'],
        widget=forms.TextInput(attrs={
            'placeholder': '8:00 AM'
        })
    )

    time_out = forms.TimeField(
        input_formats=['%I:%M %p'],
        widget=forms.TextInput(attrs={
            'placeholder': '5:00 PM'
        })
    )

    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.all().order_by('last_name', 'first_name'),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    transportation_fee_applicable = forms.BooleanField(
        required=False,
        initial=True,
        label='Transportation fee applicable for selected employees'
    )