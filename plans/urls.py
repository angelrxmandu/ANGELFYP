from django.urls import path
from . import views

app_name = 'plans'

urlpatterns = [
    path('setup/', views.setup_plan, name='setup'),
    path('<int:pk>/', views.view_plan, name='view_plan'),
    path('history/', views.plan_history, name='history'),
]
