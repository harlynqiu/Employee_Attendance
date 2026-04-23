from django import forms
from employees.models import Employee


class AttendanceSummaryForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        empty_label="All Employees"
    )

    week_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Any date within payroll week'
    )

    year = forms.IntegerField(required=False, min_value=2000)
    month = forms.IntegerField(required=False, min_value=1, max_value=12)

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )