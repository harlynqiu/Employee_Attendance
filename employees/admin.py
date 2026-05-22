from django.contrib import admin
from django.utils.html import format_html

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    list_display = (
        'employee_id',
        'last_name',
        'first_name',
        'middle_initial',
        'position',
        'salary_type',
        'rate',
        'date_started',
        'sss_number',
        'philhealth_number',
        'tin_number',
        'qr_preview_small',
    )

    readonly_fields = (
        'employee_id',
        'qr_preview',
    )

    search_fields = (
        'employee_id',
        'first_name',
        'middle_initial',
        'last_name',
        'position',
        'contact_number',
        'sss_number',
        'philhealth_number',
        'nbi_clearance_number',
        'barangay_clearance_number',
        'tin_number',
        'drivers_license_number',
    )

    list_filter = (
        'salary_type',
        'position',
        'date_started',
    )

    ordering = (
        'employee_id',
    )

    fieldsets = (
        (
            'Employee ID / QR Code',
            {
                'fields': (
                    'employee_id',
                    'qr_code',
                    'qr_preview',
                )
            }
        ),
        (
            'Personal Information',
            {
                'fields': (
                    'first_name',
                    'middle_initial',
                    'last_name',
                    'date_of_birth',
                    'citizenship',
                    'address',
                    'contact_number',
                    'spouse_name',
                    'spouse_contact_number',
                )
            }
        ),
        (
            'Educational Information',
            {
                'fields': (
                    'elementary',
                    'elementary_year',
                    'high_school',
                    'high_school_year',
                    'college',
                    'college_year',
                )
            }
        ),
        (
            'Employment History',
            {
                'fields': (
                    'company_1',
                    'company_address_1',
                    'occupation_1',
                    'years_1',
                    'company_2',
                    'company_address_2',
                    'occupation_2',
                    'years_2',
                    'company_3',
                    'company_address_3',
                    'occupation_3',
                    'years_3',
                )
            }
        ),
        (
            'Character Reference',
            {
                'fields': (
                    'reference_name_1',
                    'reference_occupation_1',
                    'reference_contact_1',
                    'reference_name_2',
                    'reference_occupation_2',
                    'reference_contact_2',
                    'reference_name_3',
                    'reference_occupation_3',
                    'reference_contact_3',
                )
            }
        ),
        (
            'Government Information',
            {
                'fields': (
                    'sss_number',
                    'sss_file',
                    'philhealth_number',
                    'philhealth_file',
                    'nbi_clearance_number',
                    'nbi_clearance_file',
                    'barangay_clearance_number',
                    'barangay_clearance_file',
                    'tin_number',
                    'tin_file',
                    'drivers_license_number',
                    'drivers_license_file',
                )
            }
        ),
        (
            'Work Position',
            {
                'fields': (
                    'position',
                    'salary_type',
                    'rate',
                    'benefits',
                    'date_started',
                )
            }
        ),
        (
            'Files',
            {
                'fields': (
                    'resume',
                )
            }
        ),
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