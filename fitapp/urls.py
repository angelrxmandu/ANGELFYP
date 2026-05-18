from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('tracker/', include('tracker.urls', namespace='tracker')),
    path('plans/', include('plans.urls', namespace='plans')),
    path('', RedirectView.as_view(url='/tracker/dashboard/', permanent=False)),
]
