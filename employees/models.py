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

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
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

    qr_code = models.ImageField(
        upload_to='employee_qrcodes/',
        blank=True,
        null=True
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        if self.rate <= 0:
            raise ValidationError({
                'rate': 'Salary rate must be greater than 0.'
            })

        if self.benefits < 0:
            raise ValidationError({
                'benefits': 'Benefits cannot be negative.'
            })

        if not self.first_name.strip():
            raise ValidationError({
                'first_name': 'First name cannot be empty.'
            })

        if not self.last_name.strip():
            raise ValidationError({
                'last_name': 'Last name cannot be empty.'
            })

        if not self.position.strip():
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
        self.full_clean()

        if not self.employee_id:
            last_employee = Employee.objects.order_by('id').last()

            if last_employee:
                last_id = int(
                    last_employee.employee_id.replace('HCQ', '')
                )
                new_id = last_id + 1
            else:
                new_id = 1

            self.employee_id = f'HCQ{new_id:04d}'

        if not self.qr_code:
            self.generate_qr_code()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"