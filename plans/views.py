from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import WeeklyPlan
from .forms import PlanSetupForm
from .recommender import generate_weekly_plan, DAYS
from tracker.models import UserProfile


@login_required
def setup_plan(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if not profile.is_complete:
        messages.warning(request, 'Please complete your profile before generating a plan.')
        return redirect('tracker:edit_profile')

    if request.method == 'POST':
        form = PlanSetupForm(request.POST)
        if form.is_valid():
            goal = form.cleaned_data['goal']
            duration = int(form.cleaned_data['duration_minutes'])
            intensity = form.cleaned_data['intensity']

            workout_plan, nutrition_plan, daily_calories, macros = generate_weekly_plan(
                profile, goal, duration, intensity,
            )

            plan = WeeklyPlan.objects.create(
                user=request.user,
                goal=goal,
                duration_minutes=duration,
                intensity=intensity,
                bmi_at_creation=profile.bmi,
                daily_calories=daily_calories,
                workout_plan=workout_plan,
                nutrition_plan=nutrition_plan,
            )
            messages.success(request, 'Your 1-week plan has been generated!')
            return redirect('plans:view_plan', pk=plan.pk)
    else:
        form = PlanSetupForm()

    return render(request, 'plans/setup.html', {'form': form, 'profile': profile})


@login_required
def view_plan(request, pk):
    plan = get_object_or_404(WeeklyPlan, pk=pk, user=request.user)
    days_data = []
    for day in DAYS:
        days_data.append({
            'name': day,
            'workout': plan.workout_plan.get(day, {}),
            'nutrition': plan.nutrition_plan.get(day, {}),
        })
    return render(request, 'plans/weekly_plan.html', {
        'plan': plan,
        'days_data': days_data,
    })


@login_required
def plan_history(request):
    plans = WeeklyPlan.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'plans/history.html', {'plans': plans})
