from django.db import models
from django.core.exceptions import ValidationError

class Employee(models.Model):
    SALARY_TYPE_CHOICES = (
        ('daily', 'Daily'),
        ('hourly', 'Hourly'),
    )

    employee_id = models.CharField(max_length=10, unique=True, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    salary_type = models.CharField(max_length=10, choices=SALARY_TYPE_CHOICES)
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    # ✅ FULL NAME PROPERTY
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    # 🔍 VALIDATION
    def clean(self):
        if self.rate <= 0:
            raise ValidationError({'rate': 'Salary rate must be greater than 0.'})

        if not self.first_name.strip():
            raise ValidationError({'first_name': 'First name cannot be empty.'})

        if not self.last_name.strip():
            raise ValidationError({'last_name': 'Last name cannot be empty.'})

        if not self.position.strip():
            raise ValidationError({'position': 'Position cannot be empty.'})

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.employee_id:
            last_employee = Employee.objects.order_by('id').last()

            if last_employee:
                last_id = int(last_employee.employee_id.replace('HCQ', ''))
                new_id = last_id + 1
            else:
                new_id = 1

            self.employee_id = f'HCQ{new_id:04d}'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"