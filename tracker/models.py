from django.db import models
from django.contrib.auth.models import User
from datetime import date


GOAL_CHOICES = [
    ('muscle_growth',     'Muscle Growth'),
    ('daily_habits',      'Improve Daily Habits'),
    ('lose_fat',          'Lose Fat'),
    ('flexibility',       'Flexibility'),
    ('strength_training', 'Strength Training'),
    ('core',              'Core'),
    ('running',           'Running'),
]

DURATION_CHOICES = [
    (15, '15 minutes / day'),
    (30, '30 minutes / day'),
    (60, '1 hour / day'),
]

GOAL_META = {
    'muscle_growth':     {'emoji': '💪', 'desc': 'Build size and strength'},
    'daily_habits':      {'emoji': '🌟', 'desc': 'Move more every day'},
    'lose_fat':          {'emoji': '🔥', 'desc': 'Burn fat, stay lean'},
    'flexibility':       {'emoji': '🧘', 'desc': 'Mobility & stretching'},
    'strength_training': {'emoji': '🏋️', 'desc': 'Power & compound lifts'},
    'core':              {'emoji': '⚡', 'desc': 'Abs & stability'},
    'running':           {'emoji': '🏃', 'desc': 'Cardio & endurance'},
}

DURATION_META = {
    15: {'emoji': '⚡', 'sub': 'Quick & efficient'},
    30: {'emoji': '🕐', 'sub': 'Balanced routine'},
    60: {'emoji': '🏆', 'sub': 'Full commitment'},
}


class UserProfile(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True, help_text='Height in centimetres')
    weight_kg = models.FloatField(null=True, blank=True, help_text='Weight in kilograms')
    preferred_goal = models.JSONField(default=list, blank=True)
    preferred_duration = models.IntegerField(null=True, blank=True, choices=DURATION_CHOICES)

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
        return all([self.gender, self.date_of_birth, self.height_cm, self.weight_kg,
                    self.preferred_goal, self.preferred_duration])

    @property
    def preferred_goal_display(self):
        labels = dict(GOAL_CHOICES)
        goals = self.preferred_goal or []
        return ', '.join(labels.get(g, g) for g in goals)

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
