from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('progress/', views.progress, name='progress'),
]
