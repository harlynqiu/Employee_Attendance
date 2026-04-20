from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from .models import Attendance


class AttendanceAdminForm(forms.ModelForm):
    time_in = forms.SplitDateTimeField(
        required=False,
        input_date_formats=['%Y-%m-%d'],
        input_time_formats=['%I:%M %p'],  # ✅ AM/PM format
        widget=AdminSplitDateTime()       # ✅ KEEP nice Django admin UI
    )

    time_out = forms.SplitDateTimeField(
        required=False,
        input_date_formats=['%Y-%m-%d'],
        input_time_formats=['%I:%M %p'],  # ✅ AM/PM format
        widget=AdminSplitDateTime()
    )

    class Meta:
        model = Attendance
        fields = '__all__'