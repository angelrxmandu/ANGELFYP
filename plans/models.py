from django.db import models
from django.contrib.auth.models import User


GOAL_CHOICES = [
    ('muscle_growth', 'Muscle Growth'),
    ('daily_habits', 'Improve Daily Habits'),
    ('lose_fat', 'Lose Fat'),
    ('flexibility', 'Flexibility'),
    ('strength_training', 'Strength Training'),
    ('core', 'Core'),
    ('running', 'Running'),
]

DURATION_CHOICES = [
    (15, '15 minutes / day'),
    (30, '30 minutes / day'),
    (60, '1 hour / day'),
]


class WeeklyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_plans')
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    duration_minutes = models.IntegerField(choices=DURATION_CHOICES)
    intensity = models.IntegerField()
    bmi_at_creation = models.FloatField(null=True, blank=True)
    daily_calories = models.IntegerField(default=0)
    workout_plan = models.JSONField(default=dict)
    nutrition_plan = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.get_goal_display()} ({self.created_at.date()})"

    @property
    def intensity_label(self):
        labels = {1: 'Very Light', 2: 'Light', 3: 'Moderate', 4: 'Hard', 5: 'Very Hard'}
        return labels.get(self.intensity, 'Moderate')
