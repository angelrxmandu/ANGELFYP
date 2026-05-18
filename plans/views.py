import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import WeeklyPlan
from .forms import PlanSetupForm
from .recommender import generate_weekly_plan, DAYS, load_foods, _pick_meal, MEAL_CALORIE_RATIO
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

            workout_plan, nutrition_plan, daily_calories, macros, explanation = generate_weekly_plan(
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
                explanation=explanation,
            )
            messages.success(request, 'Your 1-week plan has been generated!')
            return redirect('plans:view_plan', pk=plan.pk)
    else:
        initial = {}
        if profile.preferred_goal:
            initial['goal'] = profile.preferred_goal
        if profile.preferred_duration:
            initial['duration_minutes'] = profile.preferred_duration
        form = PlanSetupForm(initial=initial)

    return render(request, 'plans/setup.html', {'form': form, 'profile': profile})


@login_required
def view_plan(request, pk):
    plan = get_object_or_404(WeeklyPlan, pk=pk, user=request.user)
    completions = plan.completions or {}

    total = len(DAYS) * 4  # workout + 3 meals per day
    done = sum(1 for d in completions.values() for v in d.values() if v)
    completion_pct = round(done / total * 100) if total > 0 else 0

    days_data = []
    for day in DAYS:
        days_data.append({
            'name': day,
            'workout': plan.workout_plan.get(day, {}),
            'nutrition': plan.nutrition_plan.get(day, {}),
            'completions': completions.get(day, {}),
        })

    return render(request, 'plans/weekly_plan.html', {
        'plan': plan,
        'days_data': days_data,
        'completion_pct': completion_pct,
    })


@login_required
@require_POST
def swap_meal(request, pk):
    plan = get_object_or_404(WeeklyPlan, pk=pk, user=request.user)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    day = data.get('day')
    meal_name = data.get('meal_name')

    if day not in DAYS or meal_name not in ('Breakfast', 'Lunch', 'Dinner'):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    target_cal = int(plan.daily_calories * MEAL_CALORIE_RATIO.get(meal_name, 0.33))
    foods_df = load_foods()
    current_name = (
        plan.nutrition_plan.get(day, {}).get('meals', {}).get(meal_name, {}).get('name', '')
    )

    new_meal = None
    for _ in range(5):
        candidate = _pick_meal(foods_df, meal_name, target_cal)
        if candidate['name'] != current_name:
            new_meal = candidate
            break
    if not new_meal:
        new_meal = _pick_meal(foods_df, meal_name, target_cal)

    nutrition_plan = plan.nutrition_plan
    if day in nutrition_plan and 'meals' in nutrition_plan[day]:
        nutrition_plan[day]['meals'][meal_name] = new_meal
        plan.nutrition_plan = nutrition_plan
        plan.save(update_fields=['nutrition_plan'])

    return JsonResponse({'meal': new_meal})


@login_required
@require_POST
def toggle_completion(request, pk):
    plan = get_object_or_404(WeeklyPlan, pk=pk, user=request.user)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    day = data.get('day')
    key = data.get('key')

    valid_keys = {'workout', 'Breakfast', 'Lunch', 'Dinner'}
    if day not in DAYS or key not in valid_keys:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    completions = plan.completions or {}
    if day not in completions:
        completions[day] = {}
    completions[day][key] = not completions[day].get(key, False)
    plan.completions = completions
    plan.save(update_fields=['completions'])

    total = len(DAYS) * 4
    done = sum(1 for d in completions.values() for v in d.values() if v)
    pct = round(done / total * 100)

    return JsonResponse({'checked': completions[day][key], 'pct': pct})


@login_required
def plan_history(request):
    plans = WeeklyPlan.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'plans/history.html', {'plans': plans})
