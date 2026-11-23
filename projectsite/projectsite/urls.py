from django.contrib import admin
from django.urls import path, include
from attendance.views import unified_login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', unified_login_view, name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/', include('attendance.api_urls')),
    path('', include('attendance.urls')),
]