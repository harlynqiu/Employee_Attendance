from django.db import models
from django.core.exceptions import ValidationError
from django.core.files import File

import qrcode
from io import BytesIO
from PIL import Image


class Employee(models.Model):

    SALARY_TYPE_CHOICES = (
        ('daily', 'Daily'),
        ('hourly', 'Hourly'),
    )

    employee_id = models.CharField(
        max_length=10,
        unique=True,
        editable=False
    )

    # PERSONAL INFORMATION

    first_name = models.CharField(max_length=100)

    middle_initial = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    last_name = models.CharField(max_length=100)

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    citizenship = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    contact_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    spouse_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    spouse_contact_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # EDUCATIONAL INFORMATION

    elementary = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    elementary_year = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    high_school = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    high_school_year = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    college = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    college_year = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # EMPLOYMENT HISTORY

    company_1 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    company_address_1 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    occupation_1 = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    years_1 = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    company_2 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    company_address_2 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    occupation_2 = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    years_2 = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    company_3 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    company_address_3 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    occupation_3 = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    years_3 = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # CHARACTER REFERENCES

    reference_name_1 = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    reference_occupation_1 = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    reference_contact_1 = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    reference_name_2 = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    reference_occupation_2 = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    reference_contact_2 = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    reference_name_3 = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    reference_occupation_3 = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    reference_contact_3 = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # GOVERNMENT INFORMATION

    sss_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    sss_file = models.FileField(
        upload_to='government_documents/sss/',
        blank=True,
        null=True
    )

    philhealth_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    philhealth_file = models.FileField(
        upload_to='government_documents/philhealth/',
        blank=True,
        null=True
    )

    nbi_clearance_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    nbi_clearance_file = models.FileField(
        upload_to='government_documents/nbi/',
        blank=True,
        null=True
    )

    barangay_clearance_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    barangay_clearance_file = models.FileField(
        upload_to='government_documents/barangay/',
        blank=True,
        null=True
    )

    tin_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    tin_file = models.FileField(
        upload_to='government_documents/tin/',
        blank=True,
        null=True
    )

    drivers_license_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    drivers_license_file = models.FileField(
        upload_to='government_documents/drivers_license/',
        blank=True,
        null=True
    )

    # WORK POSITION

    position = models.CharField(max_length=100)

    salary_type = models.CharField(
        max_length=10,
        choices=SALARY_TYPE_CHOICES,
        default='daily'
    )

    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    benefits = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    date_started = models.DateField(
        blank=True,
        null=True
    )

    # FILES

    qr_code = models.ImageField(
        upload_to='employee_qrcodes/',
        blank=True,
        null=True
    )

    resume = models.FileField(
        upload_to='employee_resumes/',
        blank=True,
        null=True
    )

    @property
    def full_name(self):

        middle = (
            f" {self.middle_initial}."
            if self.middle_initial else ""
        )

        return f"{self.first_name}{middle} {self.last_name}"

    def clean(self):

        if self.rate is not None and self.rate <= 0:
            raise ValidationError({
                'rate': 'Salary rate must be greater than 0.'
            })

        if self.benefits is not None and self.benefits < 0:
            raise ValidationError({
                'benefits': 'Benefits cannot be negative.'
            })

        if not self.first_name or not self.first_name.strip():
            raise ValidationError({
                'first_name': 'First name cannot be empty.'
            })

        if not self.last_name or not self.last_name.strip():
            raise ValidationError({
                'last_name': 'Last name cannot be empty.'
            })

        if not self.position or not self.position.strip():
            raise ValidationError({
                'position': 'Position cannot be empty.'
            })

    def generate_qr_code(self):

        qr_data = self.employee_id

        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4
        )

        qr.add_data(qr_data)
        qr.make(fit=True)

        qr_image = qr.make_image(
            fill_color='black',
            back_color='white'
        ).convert('RGB')

        canvas = Image.new(
            'RGB',
            qr_image.size,
            'white'
        )

        canvas.paste(qr_image)

        filename = f'{self.employee_id}_qr.png'

        buffer = BytesIO()

        canvas.save(buffer, 'PNG')

        buffer.seek(0)

        self.qr_code.save(
            filename,
            File(buffer),
            save=False
        )

    def save(self, *args, **kwargs):

        if not self.employee_id:

            last_employee = Employee.objects.order_by('id').last()

            if last_employee and last_employee.employee_id:

                last_id = int(
                    last_employee.employee_id.replace('HCQ', '')
                )

                new_id = last_id + 1

            else:
                new_id = 1

            self.employee_id = f'HCQ{new_id:04d}'

        if not self.qr_code:
            self.generate_qr_code()

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"