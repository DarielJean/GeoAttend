from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_checkin_view, name='student-checkin'),
    path('dashboard/', views.teacher_dashboard_view, name='teacher-dashboard'),
]