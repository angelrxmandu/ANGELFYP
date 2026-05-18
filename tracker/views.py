import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, ProgressLog
from .forms import UserProfileForm, ProgressLogForm


def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@login_required
def dashboard(request):
    profile = _get_or_create_profile(request.user)
    latest_plan = request.user.weekly_plans.order_by('-created_at').first()
    logs = ProgressLog.objects.filter(user=request.user).order_by('-date')[:5]
    return render(request, 'tracker/dashboard.html', {
        'profile': profile,
        'latest_plan': latest_plan,
        'recent_logs': logs,
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
    logs = ProgressLog.objects.filter(user=request.user).order_by('date')

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
        from datetime import date
        form = ProgressLogForm(initial={'date': date.today()})

    chart_data = json.dumps({
        'labels': [str(log.date) for log in logs],
        'weights': [log.weight_kg for log in logs],
        'bmis': [log.bmi for log in logs],
    })

    return render(request, 'tracker/progress.html', {
        'form': form,
        'logs': logs,
        'profile': profile,
        'chart_data': chart_data,
    })
