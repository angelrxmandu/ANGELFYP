import json
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, ProgressLog
from .forms import UserProfileForm, ProgressLogForm
from plans.recommender import DAYS


def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _compute_streak(user):
    log_dates = set(ProgressLog.objects.filter(user=user).values_list('date', flat=True))
    streak = 0
    check = date.today()
    # If today has no log, start from yesterday so a streak yesterday still counts
    if check not in log_dates:
        check = check - timedelta(days=1)
    while check in log_dates:
        streak += 1
        check -= timedelta(days=1)
    return streak


@login_required
def dashboard(request):
    profile = _get_or_create_profile(request.user)
    latest_plan = request.user.weekly_plans.order_by('-created_at').first()
    logs = ProgressLog.objects.filter(user=request.user).order_by('-date')[:5]
    streak = _compute_streak(request.user)

    completion_pct = 0
    if latest_plan:
        completions = latest_plan.completions or {}
        total = len(DAYS) * 4
        done = sum(1 for d in completions.values() for v in d.values() if v)
        completion_pct = round(done / total * 100) if total > 0 else 0

    return render(request, 'tracker/dashboard.html', {
        'profile': profile,
        'latest_plan': latest_plan,
        'recent_logs': logs,
        'streak': streak,
        'completion_pct': completion_pct,
    })


@login_required
def edit_profile(request):
    profile = _get_or_create_profile(request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('tracker:dashboard')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'tracker/edit_profile.html', {'form': form, 'profile': profile})


@login_required
def progress(request):
    profile = _get_or_create_profile(request.user)
    logs = list(ProgressLog.objects.filter(user=request.user).order_by('date'))

    if request.method == 'POST':
        form = ProgressLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            if profile.height_cm and profile.height_cm > 0:
                h = profile.height_cm / 100
                log.bmi = round(log.weight_kg / (h ** 2), 1)
            log.save()
            profile.weight_kg = log.weight_kg
            profile.save()
            messages.success(request, 'Progress logged!')
            return redirect('tracker:progress')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProgressLogForm(initial={'date': date.today()})

    # Weight goal projection
    projection = None
    if profile.target_weight_kg and len(logs) >= 2:
        first_log, last_log = logs[0], logs[-1]
        days_elapsed = (last_log.date - first_log.date).days
        if days_elapsed > 0:
            rate = (last_log.weight_kg - first_log.weight_kg) / days_elapsed
            if rate != 0:
                days_needed = (profile.target_weight_kg - last_log.weight_kg) / rate
                if days_needed > 0:
                    eta = last_log.date + timedelta(days=int(days_needed))
                    projection = eta.strftime('%d %b %Y')

    chart_data = json.dumps({
        'labels':        [str(log.date) for log in logs],
        'weights':       [log.weight_kg for log in logs],
        'bmis':          [log.bmi for log in logs],
        'target_weight': profile.target_weight_kg,
    })

    return render(request, 'tracker/progress.html', {
        'form': form,
        'logs': logs,
        'profile': profile,
        'chart_data': chart_data,
        'projection': projection,
    })
