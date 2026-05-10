from django.contrib import admin
from django.utils.html import format_html

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    list_display = (
        'employee_id',
        'last_name',
        'first_name',
        'position',
        'salary_type',
        'rate',
        'qr_preview_small',
    )

    readonly_fields = (
        'employee_id',
        'qr_preview',
    )

    search_fields = (
        'first_name',
        'last_name',
        'employee_id',
    )

    ordering = (
        'employee_id',
    )

    fields = (
        'employee_id',
        'first_name',
        'last_name',
        'position',
        'salary_type',
        'rate',
        'benefits',
        'qr_code',
        'qr_preview',
    )

    def qr_preview(self, obj):

        if obj.qr_code:
            return format_html(
                '''
                <div style="margin-top:10px;">
                    <img src="{}"
                         width="220"
                         height="220"
                         style="
                            border:1px solid #ccc;
                            padding:10px;
                            background:white;
                         ">
                </div>
                ''',
                obj.qr_code.url
            )

        return "No QR Code Generated"

    qr_preview.short_description = "QR Code Preview"

    def qr_preview_small(self, obj):

        if obj.qr_code:
            return format_html(
                '''
                <img src="{}"
                     width="55"
                     height="55"
                     style="
                        border:1px solid #ddd;
                        padding:2px;
                        background:white;
                     ">
                ''',
                obj.qr_code.url
            )

        return "-"

    qr_preview_small.short_description = "QR"