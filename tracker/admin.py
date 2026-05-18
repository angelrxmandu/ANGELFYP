from django.contrib import admin
from .models import UserProfile, ProgressLog

admin.site.register(UserProfile)
admin.site.register(ProgressLog)
