import re
from io import BytesIO

import qrcode
from PIL import Image

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models


EMPLOYEE_ID_PREFIX = "HCQ"
EMPLOYEE_ID_DIGITS = 4


class Employee(models.Model):
    SALARY_TYPE_CHOICES = (
        ("daily", "Daily"),
        ("hourly", "Hourly"),
    )

    EMPLOYMENT_STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("RESIGNED", "Resigned"),
        ("MIA", "MIA"),
        ("TERMINATED", "Terminated"),
    )

    employee_id = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
    )

    # PERSONAL INFORMATION

    first_name = models.CharField(max_length=100)
    middle_initial = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(blank=True, null=True)
    citizenship = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=50, blank=True, null=True)
    spouse_name = models.CharField(max_length=100, blank=True, null=True)
    spouse_contact_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    # EDUCATIONAL INFORMATION

    elementary = models.CharField(max_length=255, blank=True, null=True)
    elementary_year = models.CharField(max_length=50, blank=True, null=True)
    high_school = models.CharField(max_length=255, blank=True, null=True)
    high_school_year = models.CharField(max_length=50, blank=True, null=True)
    college = models.CharField(max_length=255, blank=True, null=True)
    college_year = models.CharField(max_length=50, blank=True, null=True)

    # EMPLOYMENT HISTORY

    company_1 = models.CharField(max_length=255, blank=True, null=True)
    company_address_1 = models.CharField(max_length=255, blank=True, null=True)
    occupation_1 = models.CharField(max_length=100, blank=True, null=True)
    years_1 = models.CharField(max_length=50, blank=True, null=True)

    company_2 = models.CharField(max_length=255, blank=True, null=True)
    company_address_2 = models.CharField(max_length=255, blank=True, null=True)
    occupation_2 = models.CharField(max_length=100, blank=True, null=True)
    years_2 = models.CharField(max_length=50, blank=True, null=True)

    company_3 = models.CharField(max_length=255, blank=True, null=True)
    company_address_3 = models.CharField(max_length=255, blank=True, null=True)
    occupation_3 = models.CharField(max_length=100, blank=True, null=True)
    years_3 = models.CharField(max_length=50, blank=True, null=True)

    # CHARACTER REFERENCES

    reference_name_1 = models.CharField(max_length=100, blank=True, null=True)
    reference_occupation_1 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    reference_contact_1 = models.CharField(max_length=50, blank=True, null=True)

    reference_name_2 = models.CharField(max_length=100, blank=True, null=True)
    reference_occupation_2 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    reference_contact_2 = models.CharField(max_length=50, blank=True, null=True)

    reference_name_3 = models.CharField(max_length=100, blank=True, null=True)
    reference_occupation_3 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    reference_contact_3 = models.CharField(max_length=50, blank=True, null=True)

    # GOVERNMENT INFORMATION

    sss_number = models.CharField(max_length=100, blank=True, null=True)
    sss_file = models.FileField(
        upload_to="government_documents/sss/",
        blank=True,
        null=True,
    )
    philhealth_number = models.CharField(max_length=100, blank=True, null=True)
    philhealth_file = models.FileField(
        upload_to="government_documents/philhealth/",
        blank=True,
        null=True,
    )
    nbi_clearance_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    nbi_clearance_file = models.FileField(
        upload_to="government_documents/nbi/",
        blank=True,
        null=True,
    )
    barangay_clearance_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    barangay_clearance_file = models.FileField(
        upload_to="government_documents/barangay/",
        blank=True,
        null=True,
    )
    tin_number = models.CharField(max_length=100, blank=True, null=True)
    tin_file = models.FileField(
        upload_to="government_documents/tin/",
        blank=True,
        null=True,
    )
    drivers_license_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    drivers_license_file = models.FileField(
        upload_to="government_documents/drivers_license/",
        blank=True,
        null=True,
    )

    # WORK POSITION

    position = models.CharField(max_length=100)
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default="ACTIVE",
        db_index=True,
    )
    employment_remarks = models.TextField(blank=True, null=True)
    salary_type = models.CharField(
        max_length=10,
        choices=SALARY_TYPE_CHOICES,
        default="daily",
    )
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    benefits = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    date_started = models.DateField(blank=True, null=True)

    # FILES

    photo = models.ImageField(
        upload_to="employee_photos/",
        blank=True,
        null=True,
    )
    qr_code = models.ImageField(
        upload_to="employee_qrcodes/",
        blank=True,
        null=True,
    )
    resume = models.FileField(
        upload_to="employee_resumes/",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ("employee_id",)
        indexes = [
            models.Index(fields=("last_name", "first_name")),
        ]

    @property
    def full_name(self):
        first_name = (self.first_name or "").strip()
        last_name = (self.last_name or "").strip()
        middle_initial = (self.middle_initial or "").strip().rstrip(".")

        name_parts = [first_name]
        if middle_initial:
            name_parts.append(f"{middle_initial}.")
        name_parts.append(last_name)

        return " ".join(part for part in name_parts if part)

    @property
    def qr_contact_number(self):
        """Use the company number when configured; otherwise use the employee's."""
        company_number = getattr(
            settings,
            "HCQ_COMPANY_CONTACT_NUMBER",
            "",
        )
        return company_number or self.contact_number or "N/A"

    @property
    def qr_data(self):
        """Plain text displayed by ordinary phone QR scanners."""
        return (
            "HCQ MARKETING\n"
            f"ID: {self.employee_id}\n\n"
            f"NAME: {self.full_name.upper()}\n\n"
            f"POSITION: {self.position.strip().upper()}\n\n"
            f"CONTACT: {self.qr_contact_number}\n\n"
            "IF FOUND, PLEASE RETURN TO HCQ MARKETING"
        )

    def clean(self):
        super().clean()

        # Remove accidental spaces before validating and saving.
        for field_name in (
            "first_name",
            "middle_initial",
            "last_name",
            "position",
            "contact_number",
        ):
            value = getattr(self, field_name, None)
            if isinstance(value, str):
                setattr(self, field_name, value.strip())

        errors = {}

        if not self.first_name:
            errors["first_name"] = "First name cannot be empty."
        if not self.last_name:
            errors["last_name"] = "Last name cannot be empty."
        if not self.position:
            errors["position"] = "Position cannot be empty."
        if self.rate is not None and self.rate <= 0:
            errors["rate"] = "Salary rate must be greater than 0."
        if self.benefits is not None and self.benefits < 0:
            errors["benefits"] = "Benefits cannot be negative."

        if errors:
            raise ValidationError(errors)

    @classmethod
    def extract_employee_id_from_qr(cls, qr_value):
        """Accept both old ID-only QR codes and new multiline QR codes."""
        if not qr_value:
            return None

        qr_text = str(qr_value).strip()
        employee_pattern = rf"{re.escape(EMPLOYEE_ID_PREFIX)}\d+"

        if re.fullmatch(employee_pattern, qr_text, re.IGNORECASE):
            return qr_text.upper()

        match = re.search(
            rf"^ID:\s*({employee_pattern})\s*$",
            qr_text,
            re.IGNORECASE | re.MULTILINE,
        )
        return match.group(1).upper() if match else None

    @classmethod
    def get_next_employee_id(cls):
        """Return the next available HCQ number, ignoring malformed old IDs."""
        highest_number = 0
        pattern = re.compile(
            rf"^{re.escape(EMPLOYEE_ID_PREFIX)}(\d+)$",
            re.IGNORECASE,
        )

        employee_ids = cls.objects.filter(
            employee_id__istartswith=EMPLOYEE_ID_PREFIX,
        ).values_list("employee_id", flat=True)

        for employee_id in employee_ids.iterator():
            match = pattern.fullmatch(employee_id or "")
            if match:
                highest_number = max(highest_number, int(match.group(1)))

        return (
            f"{EMPLOYEE_ID_PREFIX}"
            f"{highest_number + 1:0{EMPLOYEE_ID_DIGITS}d}"
        )

    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(self.qr_data)
        qr.make(fit=True)

        qr_image = qr.make_image(
            fill_color="black",
            back_color="white",
        ).convert("RGB")

        # A white RGB canvas keeps the saved PNG consistent for printing.
        canvas = Image.new("RGB", qr_image.size, "white")
        canvas.paste(qr_image)

        buffer = BytesIO()
        canvas.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)

        filename = f"{self.employee_id}_qr.png"
        self.qr_code.save(filename, File(buffer), save=False)

    def qr_details_changed(self):
        if not self.pk:
            return True

        old_values = type(self).objects.filter(pk=self.pk).values(
            "employee_id",
            "first_name",
            "middle_initial",
            "last_name",
            "position",
            "contact_number",
        ).first()

        if not old_values:
            return True

        return any(
            old_values[field_name] != getattr(self, field_name)
            for field_name in old_values
        )

    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = self.get_next_employee_id()

        should_regenerate_qr = not self.qr_code or self.qr_details_changed()

        # Run model validation before creating or replacing the image file.
        self.full_clean()

        if should_regenerate_qr:
            self.generate_qr_code()

            # Ensure qr_code is saved even when save(update_fields=...) is used.
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"qr_code"}

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"