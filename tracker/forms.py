from django import forms
from .models import UserProfile, ProgressLog, GOAL_CHOICES


class UserProfileForm(forms.ModelForm):
    # Override preferred_goal as MultipleChoiceField (JSONField needs manual handling)
    preferred_goal = forms.MultipleChoiceField(
        choices=GOAL_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Preferred Goals',
    )

    class Meta:
        model = UserProfile
        fields = ['gender', 'date_of_birth', 'height_cm', 'weight_kg',
                  'preferred_goal', 'preferred_duration']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'height_cm': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 170', 'step': '0.1', 'min': '50', 'max': '300',
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 65', 'step': '0.1', 'min': '20', 'max': '500',
            }),
            'preferred_duration': forms.RadioSelect(),
        }
        labels = {
            'height_cm': 'Height (cm)',
            'weight_kg': 'Weight (kg)',
            'date_of_birth': 'Date of Birth',
            'preferred_duration': 'Workout Duration',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate checkboxes from the JSONField list stored on the instance
        if self.instance and self.instance.pk and self.instance.preferred_goal:
            self.fields['preferred_goal'].initial = self.instance.preferred_goal

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save the list directly into the JSONField
        instance.preferred_goal = self.cleaned_data.get('preferred_goal', [])
        if commit:
            instance.save()
        return instance


class ProgressLogForm(forms.ModelForm):
    class Meta:
        model = ProgressLog
        fields = ['date', 'weight_kg', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 65.5', 'step': '0.1', 'min': '20', 'max': '500',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes…',
            }),
        }
        labels = {'weight_kg': 'Weight (kg)'}
