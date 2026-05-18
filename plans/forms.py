from django import forms
from .models import WeeklyPlan, GOAL_CHOICES, DURATION_CHOICES


class PlanSetupForm(forms.Form):
    goal = forms.ChoiceField(
        choices=GOAL_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'goal-radio'}),
    )
    duration_minutes = forms.ChoiceField(
        choices=DURATION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'duration-radio'}),
        label='Daily workout duration',
    )
    intensity = forms.IntegerField(
        min_value=1,
        max_value=5,
        initial=3,
        widget=forms.NumberInput(attrs={
            'type': 'range', 'min': '1', 'max': '5', 'step': '1',
            'class': 'form-range', 'id': 'intensityRange',
        }),
    )
