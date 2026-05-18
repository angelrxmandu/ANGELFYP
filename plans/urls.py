from django.urls import path
from . import views

app_name = 'plans'

urlpatterns = [
    path('setup/', views.setup_plan, name='setup'),
    path('<int:pk>/', views.view_plan, name='view_plan'),
    path('<int:pk>/swap-meal/', views.swap_meal, name='swap_meal'),
    path('<int:pk>/toggle-completion/', views.toggle_completion, name='toggle_completion'),
    path('history/', views.plan_history, name='history'),
]
