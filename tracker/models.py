from django.db import models
from django.contrib.auth.models import User
from datetime import date


class UserProfile(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True, help_text='Height in centimetres')
    weight_kg = models.FloatField(null=True, blank=True, help_text='Weight in kilograms')

    @property
    def bmi(self):
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            h = self.height_cm / 100
            return round(self.weight_kg / (h ** 2), 1)
        return None

    @property
    def bmi_category(self):
        bmi = self.bmi
        if bmi is None:
            return None
        if bmi < 18.5:
            return 'Underweight'
        elif bmi < 25.0:
            return 'Normal weight'
        elif bmi < 30.0:
            return 'Overweight'
        return 'Obese'

    @property
    def bmi_color(self):
        bmi = self.bmi
        if bmi is None:
            return 'muted'
        if bmi < 18.5:
            return 'info'
        elif bmi < 25.0:
            return 'success'
        elif bmi < 30.0:
            return 'warning'
        return 'danger'

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return (
                today.year - self.date_of_birth.year
                - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            )
        return None

    @property
    def is_complete(self):
        return all([self.gender, self.date_of_birth, self.height_cm, self.weight_kg])

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}'s Profile"


class ProgressLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_logs')
    date = models.DateField()
    weight_kg = models.FloatField()
    bmi = models.FloatField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.email} — {self.date}: {self.weight_kg} kg"
